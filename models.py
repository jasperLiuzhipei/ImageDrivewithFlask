from datetime import datetime, UTC
from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    role = db.Column(db.String(32), default="user")


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(512), nullable=False)
    path = db.Column(db.String(1024), nullable=False)
    checksum = db.Column(db.String(64), index=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    size = db.Column(db.Integer)
    mime = db.Column(db.String(64))
    category = db.Column(db.String(128))
    tags = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class Embedding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), index=True)
    vector_ref = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class OCRText(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), index=True)
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class DownloadLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    ip = db.Column(db.String(64))
