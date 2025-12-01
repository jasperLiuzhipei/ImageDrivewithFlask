from __future__ import annotations
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, asc
from app.extensions import db
from app.models import Image, Embedding, OCRText, Tag, ImageTag
from app.utils.authz import is_admin
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

    admin = is_admin(user_id)
    q = db.session.query(Image)
    if not admin:
        q = q.filter(Image.owner_id == user_id)
    if status:
        if status.lower() == "favorite":
            fav = Tag.query.filter_by(name="favorite").first()
            if fav is None:
                q = q.filter(Image.id == -1)
            else:
                q = q.join(ImageTag, ImageTag.image_id == Image.id).filter(ImageTag.tag_id == fav.id)
        else:
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

    fav_tag = Tag.query.filter_by(name="favorite").first()
    fav_ids = set(
        r.image_id for r in db.session.query(ImageTag).filter(ImageTag.image_id.in_(ids), ImageTag.tag_id == getattr(fav_tag, "id", -1)).all()
    ) if fav_tag else set()
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
                "is_favorite": bool(i.id in fav_ids),
            }
        )
    return ok({"items": data, "total": total, "page": page, "page_size": page_size})


@images_bp.get("/<int:image_id>")
@jwt_required()
def image_detail(image_id: int):
    user_id = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    if img.owner_id != user_id and not is_admin(user_id):
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    emb = Embedding.query.filter_by(image_id=image_id).first()
    ocr = OCRText.query.filter_by(image_id=image_id).first()
    fav = Tag.query.filter_by(name="favorite").first()
    is_fav = False
    if fav is not None:
        is_fav = db.session.query(ImageTag).filter(ImageTag.image_id == image_id, ImageTag.tag_id == fav.id).first() is not None
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
            "is_favorite": bool(is_fav),
        }
    )


@images_bp.post("/<int:image_id>/favorite")
@jwt_required()
def add_favorite(image_id: int):
    uid = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img or img.owner_id != uid:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    fav = Tag.query.filter_by(name="favorite").first()
    if fav is None:
        fav = Tag(name="favorite")
        db.session.add(fav)
        db.session.commit()
    exists = db.session.query(ImageTag).filter(ImageTag.image_id == image_id, ImageTag.tag_id == fav.id).first()
    if exists is None:
        it = ImageTag(image_id=image_id, tag_id=fav.id)
        db.session.add(it)
        db.session.commit()
    return ok({"image_id": image_id, "is_favorite": True})


@images_bp.delete("/<int:image_id>/favorite")
@jwt_required()
def remove_favorite(image_id: int):
    uid = int(get_jwt_identity())
    img = Image.query.get(image_id)
    if not img or img.owner_id != uid:
        return error("IMAGE_NOT_FOUND", "图片不存在或不属于当前用户", http=404)
    fav = Tag.query.filter_by(name="favorite").first()
    if fav is None:
        return ok({"image_id": image_id, "is_favorite": False})
    row = db.session.query(ImageTag).filter(ImageTag.image_id == image_id, ImageTag.tag_id == fav.id).first()
    if row is not None:
        db.session.delete(row)
        db.session.commit()
    return ok({"image_id": image_id, "is_favorite": False})
