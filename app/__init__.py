"""Flask application factory for WebImageDrive."""
from __future__ import annotations
import os
from flask import Flask, redirect
from dotenv import load_dotenv
from .config import get_config
from .extensions import init_extensions
from .utils.errors import register_error_handlers  # new
from .blueprints.core import core_bp
from .blueprints.auth import auth_bp
from .blueprints.files import files_bp
from .blueprints.ingest import ingest_bp
from .blueprints.search import search_bp
from .blueprints.search_ocr import search_ocr_bp
from .blueprints.analytics import analytics_bp
from .blueprints.images import images_bp
from .blueprints.logs import logs_bp

BLUEPRINTS = [
    core_bp,
    auth_bp,
    files_bp,
    ingest_bp,
    search_bp,
    search_ocr_bp,
    analytics_bp,
    images_bp,
    logs_bp,
]

def register_blueprints(app: Flask) -> None:
    for bp in BLUEPRINTS:
        app.register_blueprint(bp)

def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Order:
    1. Load config
    2. Init extensions
    3. Register blueprints
    """
    # Load .env first (defaults < .env < environment variables)
    load_dotenv(override=False)

    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "dev")
    config_obj = get_config(config_name)

    # Ensure instance dir exists for default SQLite path
    try:
        os.makedirs(os.path.join(os.getcwd(), "instance"), exist_ok=True)
    except Exception:
        pass

    app = Flask(__name__)
    app.config.from_object(config_obj)

    init_extensions(app)
    # Import models so that migrations can discover them
    try:
        from . import models  # noqa: F401
    except Exception:
        pass
    # Register error handlers after extensions
    register_error_handlers(app)
    register_blueprints(app)

    # Developer-friendly root & favicon handlers to avoid confusing 404 logs
    @app.route("/")
    def _root_redirect():  # type: ignore
        return redirect("/api/v1/health", code=302)

    @app.route("/favicon.ico")
    def _favicon():  # type: ignore
        return ("", 204)

    # Minimal production safety check for SECRET_KEY
    if (config_name or "dev").lower() in {"prod", "production"}:
        if app.config.get("SECRET_KEY") in {None, "dev-secret-change-me", ""}:
            raise RuntimeError(
                "In production, SECRET_KEY must be set to a strong random value (see .env.example)"
            )

    return app

__all__ = ["create_app"]
