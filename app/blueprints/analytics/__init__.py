from __future__ import annotations
from flask import Blueprint, request, current_app, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.authz import is_admin
import os, json, datetime as dt
from app.extensions import db
from app.models import Image, Embedding, OCRText, AuditLog
from app.utils.responses import ok, error

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


@analytics_bp.get("/summary")
@jwt_required()
def summary():
    uid = int(get_jwt_identity())
    if is_admin(uid):
        imgs = Image.query.all()
    else:
        imgs = Image.query.filter_by(owner_id=uid).all()
    total = len(imgs)
    ids = [i.id for i in imgs]
    emb = db.session.query(Embedding.image_id).filter(Embedding.image_id.in_(ids)).all()
    ocr = db.session.query(OCRText.image_id).filter(OCRText.image_id.in_(ids)).all()
    has_emb = len(emb)
    has_ocr = len(ocr)
    mime_dist = {}
    for i in imgs:
        k = i.mime_type or "unknown"
        mime_dist[k] = mime_dist.get(k, 0) + 1
    days = {}
    for i in imgs:
        d = (i.created_at.date() if hasattr(i.created_at, "date") else dt.date.today()).isoformat()
        days[d] = days.get(d, 0) + 1
    dup = 0
    seen = {}
    for i in imgs:
        c = i.checksum or ""
        if c:
            n = seen.get(c, 0) + 1
            seen[c] = n
    for v in seen.values():
        if v > 1:
            dup += v
    return ok({
        "total": total,
        "mime_distribution": mime_dist,
        "daily_uploads": days,
        "embedding_coverage": {"count": has_emb, "ratio": (has_emb / total) if total else 0.0},
        "ocr_coverage": {"count": has_ocr, "ratio": (has_ocr / total) if total else 0.0},
        "duplicate_count": dup,
    })


def _dir_size(path: str) -> int:
    s = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                s += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
    return s


@analytics_bp.get("/storage")
@jwt_required()
def storage():
    uid = int(get_jwt_identity())
    up = current_app.config.get("UPLOAD_DIR")
    idx = current_app.config.get("INDEX_DIR")
    user_idx = os.path.join(idx, f"user_{uid}")
    return ok({
        "uploads_size_bytes": _dir_size(up),
        "index_size_bytes": _dir_size(user_idx),
        "index_dir": user_idx,
    })


@analytics_bp.get("/perf")
@jwt_required()
def perf():
    uid = int(get_jwt_identity())
    actions = request.args.get("actions") or "search_text,search_vector,similar_images,upload"
    keys = [a.strip() for a in actions.split(",") if a.strip()]
    q = AuditLog.query.filter(AuditLog.user_id == uid, AuditLog.action.in_(keys)).order_by(AuditLog.id.desc()).limit(1000)
    durs = {k: [] for k in keys}
    for r in q.all():
        try:
            extra = json.loads(r.extra or "{}")
            v = float(extra.get("duration_ms", 0))
            if v:
                durs[r.action].append(v)
        except Exception:
            pass
    stats = {}
    for k, arr in durs.items():
        arr = sorted(arr)
        if not arr:
            stats[k] = {"count": 0, "avg_ms": 0, "p90_ms": 0, "p99_ms": 0}
        else:
            avg = sum(arr) / len(arr)
            p90 = arr[int(0.9 * (len(arr) - 1))]
            p99 = arr[int(0.99 * (len(arr) - 1))]
            stats[k] = {"count": len(arr), "avg_ms": avg, "p90_ms": p90, "p99_ms": p99}
    return ok({"stats": stats})


@analytics_bp.get("/export.json")
@jwt_required()
def export_json():
    uid = int(get_jwt_identity())
    imgs = Image.query.filter_by(owner_id=uid).all()
    payload = [{"id": i.id, "filename": i.original_filename, "mime": i.mime_type, "created_at": i.created_at.isoformat()} for i in imgs]
    import json as _json
    text = _json.dumps({"items": payload, "count": len(payload)}, ensure_ascii=False)
    return Response(text, mimetype="application/json", headers={"Content-Disposition": "attachment; filename=analytics.json"})


@analytics_bp.get("/export.csv")
@jwt_required()
def export_csv():
    uid = int(get_jwt_identity())
    imgs = Image.query.filter_by(owner_id=uid).all()
    rows = ["id,filename,mime,created_at"]
    for i in imgs:
        rows.append(f"{i.id},{(i.original_filename or '').replace(',', ' ')},{i.mime_type or ''},{i.created_at.isoformat()}")
    text = "\n".join(rows) + "\n"
    return Response(text, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=analytics.csv"})
