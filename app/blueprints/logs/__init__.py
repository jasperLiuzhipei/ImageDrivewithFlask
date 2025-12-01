from __future__ import annotations
from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import AuditLog
from app.utils.responses import ok, error
import json

logs_bp = Blueprint("logs", __name__, url_prefix="/api/v1/logs")


@logs_bp.get("")
@jwt_required()
def list_logs():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
    except Exception:
        return error("INVALID_PAGINATION", "page/page_size 必须为整数")
    uid = int(get_jwt_identity())
    action = (request.args.get("action") or "").strip()
    q = AuditLog.query.filter(AuditLog.user_id == uid)
    if action:
        q = q.filter(AuditLog.action == action)
    q = q.order_by(AuditLog.id.desc())
    total = q.count()
    items = q.limit(page_size).offset(max(0, (page - 1) * page_size)).all()
    data = []
    for r in items:
        try:
            extra = json.loads(r.extra or "{}")
        except Exception:
            extra = {}
        data.append(
            {
                "id": r.id,
                "action": r.action,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "created_at": r.created_at.isoformat(),
                "extra": extra,
            }
        )
    return ok({"items": data, "total": total, "page": page, "page_size": page_size})


@logs_bp.post("/export")
@jwt_required()
def export_logs():
    uid = int(get_jwt_identity())
    action = (request.args.get("action") or "").strip()
    q = AuditLog.query.filter(AuditLog.user_id == uid)
    if action:
        q = q.filter(AuditLog.action == action)
    q = q.order_by(AuditLog.id.desc()).limit(5000)
    rows = ["id,action,entity_type,entity_id,created_at,extra"]
    for r in q.all():
        rows.append(
            f"{r.id},{r.action},{r.entity_type or ''},{r.entity_id or ''},{r.created_at.isoformat()},{(r.extra or '').replace(',', ' ')}"
        )
    text = "\n".join(rows) + "\n"
    return Response(text, mimetype="text/csv")
