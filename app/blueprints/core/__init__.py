from __future__ import annotations
from flask import Blueprint, jsonify, current_app
import sys
from importlib.util import find_spec
from app.utils.errors import AppError
from app.services import clip_runtime

core_bp = Blueprint("core", __name__, url_prefix="/api/v1")


@core_bp.get("/")
def index():
    return jsonify(
        {
            "status": "ok",
            "service": current_app.config.get("APP_NAME", "WebImageDrive"),
            "version": current_app.config.get("APP_VERSION", "0.1.0"),
        }
    )


@core_bp.get("/health")
def health():
    # Enrich health info with runtime diagnostics
    info = {
        "status": "healthy",
        "python": sys.version.split()[0],
        "app_version": current_app.config.get("APP_VERSION", "unknown"),
    }
    # Optional: presence checks (no heavy imports)
    for mod in ("torch", "faiss", "sentence_transformers", "doctr"):
        info[f"has_{mod}"] = bool(find_spec(mod))
    # faiss sometimes exposed as faiss_cpu
    info["has_faiss"] = info.get("has_faiss", False) or bool(find_spec("faiss_cpu"))
    # Report numpy version to help diagnose ABI issues
    try:
        import numpy as _np  # type: ignore

        info["numpy_version"] = _np.__version__
    except Exception:
        info["numpy_version"] = None
    # Report configured embedding backend (without forcing model load)
    try:
        info["embedding_backend_config"] = (
            "team-processor" if current_app.config.get("USE_TEAM_CLIP") else "sentence-transformers"
        )
        info["embedding_backend_loaded"] = clip_runtime.embedding_backend()
        info["embedding_dim"] = clip_runtime.embedding_dim()
    except Exception:
        pass
    return jsonify(info)


@core_bp.get("/boom")
def boom():
    # App-defined business error
    raise AppError("DEMO_ERROR", "Just a test", http=418)


@core_bp.get("/crash")
def crash():
    # Uncaught exception to test 500 handler
    1 / 0  # noqa: B018
