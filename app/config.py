"""Application configuration classes.

Precedence of settings:
1) Hard-coded defaults in Config classes
2) .env loaded by python-dotenv (if present)
3) Real environment variables (highest priority)

Environment variable FLASK_CONFIG selects: dev | prod | test (default: dev)
"""
from __future__ import annotations
import os


class Config:
    # Core
    APP_NAME = "WebImageDrive"
    APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Database (default to sqlite for minimal setup)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(os.getcwd(), 'instance', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_TOKEN_LOCATION = ["headers", "query_string"]
    JWT_QUERY_STRING_NAME = os.environ.get("JWT_QUERY_STRING_NAME", "jwt")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))  # seconds

    # CORS (placeholder)
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Uploads (local storage defaults)
    UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))
    # Max upload size in MB; also map to Flask MAX_CONTENT_LENGTH (bytes)
    UPLOAD_MAX_SIZE_MB = float(os.environ.get("UPLOAD_MAX_SIZE_MB", "20"))
    MAX_CONTENT_LENGTH = int(UPLOAD_MAX_SIZE_MB * 1024 * 1024)
    # Comma-separated allowed mime types
    UPLOAD_ALLOWED_MIME = [
        m.strip() for m in os.environ.get(
            "UPLOAD_ALLOWED_MIME", "image/jpeg,image/png,image/webp,image/gif"
        ).split(",") if m.strip()
    ]

    # Celery (optional; not required to run the minimal app)
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # CLIP model (for online embedding)
    CLIP_MODEL_NAME = os.environ.get("CLIP_MODEL_NAME", "clip-ViT-B-32")
    # Toggle to use teammate's EmbeddingProcessor instead of built-in runtime
    USE_TEAM_CLIP = os.environ.get("USE_TEAM_CLIP", "0").lower() in {"1", "true", "yes"}
    # Optional override for teammate processor path (defaults to repo path)
    TEAM_CLIP_PROCESSOR_PATH = os.environ.get("TEAM_CLIP_PROCESSOR_PATH", "")

    # FAISS index persistence (per-user) directory
    INDEX_DIR = os.environ.get("INDEX_DIR", os.path.join(os.getcwd(), "instance", "faiss"))


class DevConfig(Config):
    DEBUG = True


class ProdConfig(Config):
    DEBUG = False


class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def get_config(name: str | None):
    key = (name or "dev").lower()
    mapping = {
        "dev": DevConfig,
        "development": DevConfig,
        "prod": ProdConfig,
        "production": ProdConfig,
        "test": TestConfig,
        "testing": TestConfig,
    }
    return mapping.get(key, DevConfig)
