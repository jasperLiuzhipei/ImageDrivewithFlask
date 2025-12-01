from __future__ import annotations
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.authz import is_admin
from sqlalchemy import or_
from app.models import OCRText, Image
from app.utils.responses import ok, error

search_ocr_bp = Blueprint("search_ocr", __name__, url_prefix="/api/v1/search/ocr")


@search_ocr_bp.post("")
@jwt_required()
def search_ocr():
    """Simple OCR text search over user's images.

    Request JSON:
    - query: str (required)
    - top_k: int (optional, default 20)
    """
    data = request.get_json(silent=True) or {}
    q = (data.get("query") or "").strip()
    if not q:
        return error("INVALID_QUERY", "query 不能为空")
    try:
        top_k = int(data.get("top_k", 20))
    except Exception:
        top_k = 20

    owner_id = int(get_jwt_identity())
    admin = is_admin(owner_id)

    # 管理员可检索所有；普通用户仅检索自己的图片
    qset = OCRText.query.join(Image, OCRText.image_id == Image.id)
    if not admin:
        qset = qset.filter(Image.owner_id == owner_id)
    items = (
        qset.filter(OCRText.text.ilike(f"%{q}%"))
        .order_by(OCRText.id.desc())
        .limit(max(1, min(200, top_k)))
        .all()
    )

    results = []
    for row in items:
        txt = row.text or ""
        idx = txt.lower().find(q.lower())
        start = max(0, idx - 30) if idx >= 0 else 0
        end = min(len(txt), (idx + len(q) + 30) if idx >= 0 else 120)
        snippet = txt[start:end]
        img = Image.query.get(int(row.image_id))
        results.append(
            {
                "image_id": int(row.image_id),
                "snippet": snippet,
                "original_filename": getattr(img, "original_filename", None),
                "mime_type": getattr(img, "mime_type", None),
                "thumb_url": f"/api/v1/files/{int(row.image_id)}/thumb",
                "download_url": f"/api/v1/files/{int(row.image_id)}/download",
            }
        )

    return ok({"query": q, "results": results, "count": len(results)})
