from __future__ import annotations
import os
from typing import List
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Image, Embedding, OCRText
from app.services.ocr import extract_text as ocr_extract, extract_text_batch as ocr_extract_batch
from app.services.embedding_io import l2_normalize, to_bytes
from app.utils.responses import ok, error

ingest_bp = Blueprint("ingest", __name__, url_prefix="/api/v1/ingest")


@ingest_bp.post("/embedding")
@jwt_required()
def ingest_embedding():
    """Create or update an image embedding for the current user.

    Request JSON:
    - image_id: int (required)
    - vector: list[float] (required)
    - model_version: str (optional, default: model on existing row or 'clip-vit-b32')
    - normalized: bool (optional, default False)  # if False, we will L2-normalize

    Behavior:
    - Verifies the image exists and is owned by current user
    - Normalizes vector unless `normalized` is True
    - Upsert on `embeddings.image_id` (unique): insert or update vec/dim/model_version
    """
    data = request.get_json(silent=True) or {}
    try:
        image_id = int(data.get("image_id"))
    except Exception:
        return error("INVALID_IMAGE_ID", "image_id 必须为整数")

    vector = data.get("vector")
    if not isinstance(vector, list) or len(vector) == 0:
        return error("INVALID_VECTOR", "vector 必须为非空数组")

    normalized = bool(data.get("normalized", False))
    model_version = (data.get("model_version") or "clip-vit-b32").strip()

    # Ownership check
    owner_id = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img or img.owner_id != owner_id:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)

    # Normalize if needed
    vec: List[float] = vector if normalized else l2_normalize(vector)
    dim = len(vec)
    try:
        payload = to_bytes(vec)
    except Exception:
        return error("VECTOR_ENCODE_ERROR", "向量序列化失败，请检查数值是否为可转为 float 的类型")

    emb = Embedding.query.filter_by(image_id=image_id).first()
    created = False
    if emb is None:
        emb = Embedding(image_id=image_id, vec=payload, dim=dim, model_version=model_version)
        db.session.add(emb)
        created = True
    else:
        emb.vec = payload
        emb.dim = dim
        if model_version:
            emb.model_version = model_version

    db.session.commit()

    return ok(
        {
            "image_id": image_id,
            "dim": dim,
            "model_version": emb.model_version,
            "created": created,
        }
    )


@ingest_bp.post("/embedding/batch")
@jwt_required()
def ingest_embedding_batch():
    """Batch upsert embeddings.

    Request JSON:
    - items: [ { image_id, vector, model_version?, normalized? }, ... ]
    Returns per-item status for simple client-side aggregation.
    """
    data = request.get_json(silent=True) or {}
    items = data.get("items")
    if not isinstance(items, list) or len(items) == 0:
        return error("INVALID_ITEMS", "items 必须为非空数组")

    owner_id = int(get_jwt_identity())
    results = []
    for idx, item in enumerate(items):
        try:
            image_id = int(item.get("image_id"))
            vector = item.get("vector")
            if not isinstance(vector, list) or len(vector) == 0:
                raise ValueError("vector 必须为非空数组")
            normalized = bool(item.get("normalized", False))
            model_version = (item.get("model_version") or "clip-vit-b32").strip()

            img = Image.query.get(image_id)
            if not img or img.owner_id != owner_id:
                results.append({"image_id": image_id, "ok": False, "error": "IMAGE_NOT_FOUND"})
                continue

            vec = vector if normalized else l2_normalize(vector)
            payload = to_bytes(vec)
            dim = len(vec)

            emb = Embedding.query.filter_by(image_id=image_id).first()
            created = False
            if emb is None:
                emb = Embedding(image_id=image_id, vec=payload, dim=dim, model_version=model_version)
                db.session.add(emb)
                created = True
            else:
                emb.vec = payload
                emb.dim = dim
                if model_version:
                    emb.model_version = model_version

            results.append({"image_id": image_id, "ok": True, "created": created, "dim": dim})
        except Exception as e:  # capture any per-item failure but continue others
            results.append({"index": idx, "ok": False, "error": str(e)})

    db.session.commit()
    return ok({"results": results})


@ingest_bp.post("/ocr")
@jwt_required()
def ingest_ocr():
    """Run OCR for a given image owned by current user and persist OCRText.

    Request JSON:
    - image_id: int (required)
    - include_text: bool (optional, default False)  是否在响应中返回文本预览
    - snippet_len: int (optional, default 120)      文本预览最大长度
    Behavior:
    - Resolve local path from storage_uri (local://<name>) using UPLOAD_DIR
    - Run OCR best-effort; if no text, returns ok with has_text=false
    - Upsert into OCRText table
    """
    data = request.get_json(silent=True) or {}
    try:
        image_id = int(data.get("image_id"))
    except Exception:
        return error("INVALID_IMAGE_ID", "image_id 必须为整数")
    include_text = bool(data.get("include_text", False))
    snippet_len = int(data.get("snippet_len", 120))

    owner_id = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img or img.owner_id != owner_id:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)

    # Resolve local path
    storage_uri = img.storage_uri or ""
    local_path = None
    if storage_uri.startswith("local://"):
        fname = storage_uri[len("local://") :]
        local_path = os.path.join(current_app.config.get("UPLOAD_DIR"), fname)
    else:
        return error("UNSUPPORTED_STORAGE", "当前仅支持本地存储的 OCR")

    if not os.path.exists(local_path):
        return error("FILE_NOT_FOUND", "文件不存在，无法进行 OCR", http=404)

    text = ocr_extract(local_path) or ""

    row = OCRText.query.filter_by(image_id=image_id).first()
    created = False
    if row is None:
        row = OCRText(image_id=image_id, text=text or None, avg_confidence=None)
        db.session.add(row)
        created = True
    else:
        row.text = text or None
    db.session.commit()

    payload = {"image_id": image_id, "has_text": bool(text), "created": created}
    if include_text:
        preview = text
        if snippet_len > 0 and len(preview) > snippet_len:
            preview = preview[:snippet_len]
        payload["text_preview"] = preview

    return ok(payload)


@ingest_bp.post("/ocr/batch")
@jwt_required()
def ingest_ocr_batch():
    """Batch OCR for multiple images owned by current user.

    Request JSON:
    - image_ids: [int, ...]  或  items: [{image_id:int}, ...]
    - batch_size: int (optional, default 32) 传递给组员的批处理函数（若存在）

    Behavior:
    - 仅处理当前用户拥有的本地存储图片（storage_uri=local://...），跳过不合法项
    - 调用组员的批处理接口（若可用），否则逐张处理
    - 将结果写入/更新 OCRText，返回逐项状态
    """
    data = request.get_json(silent=True) or {}
    image_ids = data.get("image_ids")
    if not isinstance(image_ids, list):
        items = data.get("items") or []
        if isinstance(items, list):
            image_ids = [i.get("image_id") for i in items if isinstance(i, dict) and "image_id" in i]
    if not isinstance(image_ids, list) or len(image_ids) == 0:
        return error("INVALID_IMAGE_IDS", "image_ids 必须为非空数组")

    # sanitize ids
    ids: List[int] = []
    for v in image_ids:
        try:
            ids.append(int(v))
        except Exception:
            continue
    if not ids:
        return error("INVALID_IMAGE_IDS", "image_ids 解析失败")

    batch_size = int(data.get("batch_size", 32))
    include_text = bool(data.get("include_text", False))
    snippet_len = int(data.get("snippet_len", 120))

    owner_id = int(get_jwt_identity())
    # Gather local file paths for owned images
    id_to_path = {}
    missing_or_forbidden = set()
    for iid in ids:
        img = Image.query.get(iid)
        if not img or img.owner_id != owner_id:
            missing_or_forbidden.add(iid)
            continue
        storage_uri = img.storage_uri or ""
        if not storage_uri.startswith("local://"):
            missing_or_forbidden.add(iid)
            continue
        fname = storage_uri[len("local://"):]
        local_path = os.path.join(current_app.config.get("UPLOAD_DIR"), fname)
        if not os.path.exists(local_path):
            missing_or_forbidden.add(iid)
            continue
        id_to_path[iid] = local_path

    # Maintain ordering for mapping back results
    ok_ids = list(id_to_path.keys())
    paths = [id_to_path[i] for i in ok_ids]

    results = []
    texts: List[str | None] = []
    if paths:
        outs = ocr_extract_batch(paths, batch_size=batch_size) or []
        # normalize length
        if len(outs) != len(paths):
            # fallback: per-image
            outs = [ocr_extract(p) for p in paths]
        texts = [o or "" for o in outs]

    # Upsert DB per successful mapped item
    for iid, text in zip(ok_ids, texts):
        row = OCRText.query.filter_by(image_id=iid).first()
        created = False
        if row is None:
            row = OCRText(image_id=iid, text=(text or None), avg_confidence=None)
            db.session.add(row)
            created = True
        else:
            row.text = text or None
        item = {"image_id": iid, "ok": True, "created": created, "has_text": bool(text)}
        if include_text:
            preview = (text or "")
            if snippet_len > 0 and len(preview) > snippet_len:
                preview = preview[:snippet_len]
            item["text_preview"] = preview
        results.append(item)

    # Append errors for missing/forbidden
    for iid in sorted(missing_or_forbidden):
        results.append({"image_id": iid, "ok": False, "error": "IMAGE_NOT_FOUND_OR_UNSUPPORTED"})

    db.session.commit()
    # Keep client-friendly ordering: requested order if possible
    order = {iid: idx for idx, iid in enumerate(ids)}
    results.sort(key=lambda r: order.get(r.get("image_id"), 10**9))
    return ok({"results": results, "batch_size": batch_size, "include_text": include_text, "snippet_len": snippet_len})
