from __future__ import annotations
import json
from flask import request
from app.extensions import db
from app.models import AuditLog


def write_audit(user_id: int | None, action: str, entity_type: str | None = None, entity_id: int | None = None, extra: dict | None = None) -> None:
    try:
        ip = request.headers.get("X-Forwarded-For") or request.remote_addr or ""
        ua = request.headers.get("User-Agent") or ""
        row = AuditLog(
            user_id=int(user_id) if user_id is not None else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip=ip,
            user_agent=ua,
            extra=json.dumps(extra or {}, ensure_ascii=False),
        )
        db.session.add(row)
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
