from __future__ import annotations
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, asc
from app.extensions import db
from app.models import Image, Embedding, OCRText
from app.utils.responses import ok, error

images_bp = Blueprint("images", __name__, url_prefix="/api/v1/images")


@images_bp.get("")
@jwt_required()
def list_images():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except Exception:
        return error("INVALID_PAGINATION", "page/page_size 必须为整数")
    order_by = (request.args.get("order_by") or "created_at").strip()
    order = (request.args.get("order") or "desc").lower()
    status = (request.args.get("status") or "").strip()
    mime = (request.args.get("mime") or "").strip()

    user_id = int(get_jwt_identity())

    q = db.session.query(Image).filter(Image.owner_id == user_id)
    if status:
        q = q.filter(Image.status == status)
    if mime:
        q = q.filter(Image.mime_type == mime)

    col = getattr(Image, order_by, Image.created_at)
    q = q.order_by(desc(col) if order == "desc" else asc(col))

    total = q.count()
    items = (
        q.limit(page_size).offset(max(0, (page - 1) * page_size)).all()
    )

    ids = [i.id for i in items]
    emb_map = {r.image_id: r for r in db.session.query(Embedding).filter(Embedding.image_id.in_(ids)).all()}
    ocr_map = {r.image_id: r for r in db.session.query(OCRText).filter(OCRText.image_id.in_(ids)).all()}

    data = []
    for i in items:
        data.append(
            {
                "id": i.id,
                "original_filename": i.original_filename,
                "mime_type": i.mime_type,
                "status": i.status,
                "visibility": i.visibility,
                "created_at": i.created_at.isoformat(),
                "has_embedding": bool(emb_map.get(i.id)),
                "has_ocr_text": bool(ocr_map.get(i.id)),
                "download_url": f"/api/v1/files/{i.id}/download",
                "thumb_url": f"/api/v1/files/{i.id}/thumb",
            }
        )
    return ok({"items": data, "total": total, "page": page, "page_size": page_size})


@images_bp.get("/<int:image_id>")
@jwt_required()
def image_detail(image_id: int):
    user_id = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img or img.owner_id != user_id:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    emb = Embedding.query.filter_by(image_id=image_id).first()
    ocr = OCRText.query.filter_by(image_id=image_id).first()
    return ok(
        {
            "id": img.id,
            "original_filename": img.original_filename,
            "mime_type": img.mime_type,
            "width": img.width,
            "height": img.height,
            "status": img.status,
            "visibility": img.visibility,
            "created_at": img.created_at.isoformat(),
            "checksum": img.checksum,
            "has_embedding": bool(emb),
            "embedding_dim": int(getattr(emb, "dim", 0) or 0),
            "has_ocr_text": bool(ocr),
            "download_url": f"/api/v1/files/{img.id}/download",
            "thumb_url": f"/api/v1/files/{img.id}/thumb",
        }
    )

