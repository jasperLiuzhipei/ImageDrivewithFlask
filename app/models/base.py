"""Common mixins for SQLAlchemy models."""
from __future__ import annotations
import datetime as dt
from app.extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False
    )


class SoftDeleteMixin:
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
