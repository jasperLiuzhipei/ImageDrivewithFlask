"""SQLAlchemy models for WebImageDrive (initial minimal draft).

Notes:
- This draft favors clarity; later we can refine indexes (e.g., text search) and constraints.
- Embedding vectors stored separately (Embedding) referencing Image.
"""
from __future__ import annotations
import datetime as dt
from typing import Optional
from app.extensions import db  # use app-wide SQLAlchemy instance

__all__ = [
    "User",
    "Image",
    "Embedding",
    "OCRText",
    "Tag",
    "ImageTag",
    "AuditLog",
]


class User(db.Model):  # type: ignore
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    images = db.relationship("Image", back_populates="owner", lazy="dynamic")


class Image(db.Model):  # type: ignore
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    storage_uri = db.Column(db.String(512), nullable=False, unique=True)
    mime_type = db.Column(db.String(64), nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    checksum = db.Column(db.String(64), nullable=True, index=True)  # sha256 or md5
    status = db.Column(db.String(32), nullable=False, default="READY", index=True)
    visibility = db.Column(db.String(32), nullable=False, default="private", index=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)

    owner = db.relationship("User", back_populates="images")
    embedding = db.relationship("Embedding", back_populates="image", uselist=False, lazy="select")
    ocr_text = db.relationship("OCRText", back_populates="image", uselist=False, lazy="select")
    tags = db.relationship("ImageTag", back_populates="image", lazy="dynamic")


class Embedding(db.Model):  # type: ignore
    __tablename__ = "embeddings"
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"), nullable=False, unique=True, index=True)
    # Store normalized embedding as binary blob (e.g., 512 * float32). Later: switch to array type if needed.
    vec = db.Column(db.LargeBinary, nullable=False)
    dim = db.Column(db.Integer, nullable=False)
    model_version = db.Column(db.String(64), nullable=False, default="clip-vit-b32")
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)

    image = db.relationship("Image", back_populates="embedding")


class OCRText(db.Model):  # type: ignore
    __tablename__ = "ocr_texts"
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"), nullable=False, unique=True, index=True)
    text = db.Column(db.Text, nullable=True)
    avg_confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)

    image = db.relationship("Image", back_populates="ocr_text")


class Tag(db.Model):  # type: ignore
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)


class ImageTag(db.Model):  # type: ignore
    __tablename__ = "image_tags"
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey("images.id"), nullable=False, index=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)

    # Could add uniqueness constraint later: (image_id, tag_id)
    image = db.relationship("Image", back_populates="tags")
    tag = db.relationship("Tag")


class AuditLog(db.Model):  # type: ignore
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    entity_type = db.Column(db.String(64), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    extra = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False, index=True)

    user = db.relationship("User")
