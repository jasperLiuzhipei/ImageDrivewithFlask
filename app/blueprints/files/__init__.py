from __future__ import annotations
import os
import uuid
import hashlib
from typing import Tuple
from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Image, Embedding, OCRText, ImageTag
from app.services.clip_runtime import embed_image_path
from app.utils.authz import is_admin
from app.services import index_store
from app.services.ocr import extract_text as ocr_extract
from app.services.embedding_io import l2_normalize, to_bytes
from app.utils.responses import ok, error
from app.utils.audit import write_audit

files_bp = Blueprint("files", __name__, url_prefix="/api/v1/files")


def _ensure_upload_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _compute_sha256(stream) -> str:
    pos = stream.tell() if stream.seekable() else None
    h = hashlib.sha256()
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        h.update(chunk)
    if pos is not None:
        stream.seek(pos)
    return h.hexdigest()


@files_bp.post("/upload")
@jwt_required()
def upload_file():
    # Validate file presence
    if "file" not in request.files:
        return error("NO_FILE", "未找到文件字段 'file'")
    file = request.files["file"]
    if not file or file.filename == "":
        return error("EMPTY_FILE", "文件为空")

    # Validate size (Flask will also enforce MAX_CONTENT_LENGTH)
    # Validate mime
    allowed = current_app.config.get("UPLOAD_ALLOWED_MIME", [])
    mime = file.mimetype or ""
    if allowed and mime not in allowed:
        return error("INVALID_MIME", f"不支持的文件类型: {mime}")

    # Prepare paths
    upload_dir = current_app.config.get("UPLOAD_DIR")
    _ensure_upload_dir(upload_dir)

    # Filename handling
    original_name = file.filename
    ext = os.path.splitext(secure_filename(original_name))[-1].lower()
    new_name = f"{uuid.uuid4().hex}{ext}"
    abs_path = os.path.join(upload_dir, new_name)

    # Compute checksum before saving (read stream, then save)
    checksum = _compute_sha256(file.stream)
    file.stream.seek(0)
    file.save(abs_path)

    # Persist image record
    owner_id = int(get_jwt_identity())
    img = Image(
        owner_id=owner_id,
        original_filename=original_name,
        storage_uri=f"local://{new_name}",
        mime_type=mime,
        checksum=checksum,
        status="READY",
        visibility="private",
    )
    db.session.add(img)
    db.session.commit()

    # Online embedding (best-effort; if deps missing or model load fails, we just skip)
    abs_public_path = abs_path  # currently local storage; could map from storage_uri later
    vec = embed_image_path(abs_public_path)
    if vec:
        norm_vec = l2_normalize(vec)
        payload = to_bytes(norm_vec)
        emb = Embedding(image_id=img.id, vec=payload, dim=len(norm_vec), model_version=current_app.config.get("CLIP_MODEL_NAME", "clip-ViT-B-32"))
        db.session.add(emb)
        db.session.commit()
    # Best-effort OCR
    try:
        text = ocr_extract(abs_public_path)
        row = OCRText.query.filter_by(image_id=img.id).first()
        if row is None and text:
            row = OCRText(image_id=img.id, text=text, avg_confidence=None)
            db.session.add(row)
            db.session.commit()
        elif row is not None:
            row.text = text or row.text
            db.session.commit()
    except Exception:
        # Silent skip
        pass

    # TODO: dispatch async tasks (generate thumbnails, OCR)

    payload = {
        "image_id": img.id,
        "original_filename": img.original_filename,
        "storage_uri": img.storage_uri,
        "mime_type": img.mime_type,
        "checksum": img.checksum,
        "status": img.status,
        "visibility": img.visibility,
        "has_embedding": bool(vec),
        "has_ocr_text": bool(text) if 'text' in locals() else False,
    }
    try:
        write_audit(owner_id, "upload", "image", img.id, {"mime": mime})
    except Exception:
        pass
    return ok(payload)

@files_bp.post("/upload/batch")
@jwt_required()
def upload_batch():
    owner_id = int(get_jwt_identity())
    upload_dir = current_app.config.get("UPLOAD_DIR")
    _ensure_upload_dir(upload_dir)
    files = request.files.getlist("files")
    if not files:
        files = list(request.files.values())
    if not files:
        return error("NO_FILE", "未找到文件字段 'files'")
    results = []
    for file in files:
        if not file or file.filename == "":
            continue
        allowed = current_app.config.get("UPLOAD_ALLOWED_MIME", [])
        mime = file.mimetype or ""
        if allowed and mime not in allowed:
            continue
        original_name = file.filename
        ext = os.path.splitext(secure_filename(original_name))[-1].lower()
        new_name = f"{uuid.uuid4().hex}{ext}"
        abs_path = os.path.join(upload_dir, new_name)
        checksum = _compute_sha256(file.stream)
        file.stream.seek(0)
        file.save(abs_path)
        img = Image(
            owner_id=owner_id,
            original_filename=original_name,
            storage_uri=f"local://{new_name}",
            mime_type=mime,
            checksum=checksum,
            status="READY",
            visibility="private",
        )
        db.session.add(img)
        db.session.commit()
        vec = embed_image_path(abs_path)
        if vec:
            norm_vec = l2_normalize(vec)
            payload = to_bytes(norm_vec)
            emb = Embedding(image_id=img.id, vec=payload, dim=len(norm_vec), model_version=current_app.config.get("CLIP_MODEL_NAME", "clip-ViT-B-32"))
            db.session.add(emb)
            db.session.commit()
        try:
            text = ocr_extract(abs_path)
            row = OCRText.query.filter_by(image_id=img.id).first()
            if row is None and text:
                row = OCRText(image_id=img.id, text=text, avg_confidence=None)
                db.session.add(row)
                db.session.commit()
            elif row is not None:
                row.text = text or row.text
                db.session.commit()
        except Exception:
            pass
        results.append({
            "image_id": img.id,
            "original_filename": img.original_filename,
            "storage_uri": img.storage_uri,
            "mime_type": img.mime_type,
            "checksum": img.checksum,
            "status": img.status,
            "visibility": img.visibility,
        })
        try:
            write_audit(owner_id, "upload", "image", img.id, {"mime": mime})
        except Exception:
            pass
    try:
        index_store.rebuild_index(owner_id)
    except Exception:
        pass
    return ok({"items": results, "count": len(results)})

@files_bp.get("/<int:image_id>/download")
@jwt_required()
def download_file(image_id: int):
    from flask import send_file
    owner_id = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    if img.owner_id != owner_id and not is_admin(owner_id):
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    uri = img.storage_uri or ""
    if not uri.startswith("local://"):
        return error("UNSUPPORTED_STORAGE", "当前仅支持本地存储的下载")
    fname = uri[len("local://"):]
    path = os.path.join(current_app.config.get("UPLOAD_DIR"), fname)
    if not os.path.exists(path):
        return error("FILE_NOT_FOUND", "文件不存在", http=404)
    resp = send_file(path, as_attachment=True, download_name=img.original_filename or fname)
    try:
        write_audit(owner_id, "download", "image", img.id, {})
    except Exception:
        pass
    return resp

@files_bp.get("/<int:image_id>/thumb")
@jwt_required()
def thumbnail(image_id: int):
    from flask import send_file
    owner_id = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    if img.owner_id != owner_id and not is_admin(owner_id):
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    uri = img.storage_uri or ""
    if not uri.startswith("local://"):
        return error("UNSUPPORTED_STORAGE", "当前仅支持本地存储的缩略图")
    fname = uri[len("local://"):]
    root = current_app.config.get("UPLOAD_DIR")
    src = os.path.join(root, fname)
    if not os.path.exists(src):
        return error("FILE_NOT_FOUND", "文件不存在", http=404)
    thumbs = os.path.join(root, "thumbs")
    os.makedirs(thumbs, exist_ok=True)
    out = os.path.join(thumbs, f"{image_id}.jpg")
    if not os.path.exists(out):
        try:
            from PIL import Image as PILImage  # type: ignore
            with PILImage.open(src) as im:
                im = im.convert("RGB")
                im.thumbnail((256, 256))
                im.save(out, format="JPEG", quality=85)
        except Exception:
            return error("THUMB_FAIL", "缩略图生成失败")
    resp = send_file(out, mimetype="image/jpeg")
    try:
        write_audit(owner_id, "thumb", "image", img.id, {})
    except Exception:
        pass
    return resp

@files_bp.delete("/<int:image_id>")
@jwt_required()
def delete_image(image_id: int):
    owner_id = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    if img.owner_id != owner_id and not is_admin(owner_id):
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    uri = img.storage_uri or ""
    if uri.startswith("local://"):
        fname = uri[len("local://"):]
        root = current_app.config.get("UPLOAD_DIR")
        src = os.path.join(root, fname)
        try:
            if os.path.exists(src):
                os.remove(src)
        except Exception:
            pass
        thumbs = os.path.join(root, "thumbs")
        tpath = os.path.join(thumbs, f"{image_id}.jpg")
        try:
            if os.path.exists(tpath):
                os.remove(tpath)
        except Exception:
            pass
    emb = Embedding.query.filter_by(image_id=image_id).first()
    if emb:
        db.session.delete(emb)
    ocr = OCRText.query.filter_by(image_id=image_id).first()
    if ocr:
        db.session.delete(ocr)
    try:
        db.session.query(ImageTag).filter(ImageTag.image_id == image_id).delete(synchronize_session=False)
    except Exception:
        pass
    db.session.delete(img)
    db.session.commit()
    try:
        index_store.rebuild_index(img.owner_id)
        write_audit(owner_id, "delete", "image", image_id, {})
    except Exception:
        pass
    return ok({"image_id": image_id, "deleted": True})
