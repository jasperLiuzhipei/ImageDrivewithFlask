"""Error handling and trace_id injection.

Provides:
- AppError: custom exception with code/message/http status
- register_error_handlers(app): install before/after hooks and handlers
"""
from __future__ import annotations
import uuid
import logging
from typing import Any
from flask import g, request
from werkzeug.exceptions import HTTPException
from .responses import error as error_resp


log = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, code: str, message: str, *, http: int = 400, details: Any | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http = http
        self.details = details


def register_error_handlers(app):
    @app.before_request
    def _inject_trace_id():  # pragma: no cover - lightweight
        # Simple request-scoped trace id
        g.trace_id = uuid.uuid4().hex

    @app.errorhandler(AppError)
    def _handle_app_error(e: AppError):
        return error_resp(e.code, e.message, details=e.details, http=e.http, trace_id=getattr(g, "trace_id", None))

    @app.errorhandler(HTTPException)
    def _handle_http_error(e: HTTPException):
        code = getattr(e, "name", "HTTP_ERROR") or "HTTP_ERROR"
        message = getattr(e, "description", str(e))
        return error_resp(code, message, http=e.code or 500, trace_id=getattr(g, "trace_id", None))

    @app.errorhandler(Exception)
    def _handle_unexpected(e: Exception):
        log.exception("Unhandled exception: %s", e)
        return error_resp("INTERNAL_ERROR", "Unexpected server error", http=500, trace_id=getattr(g, "trace_id", None))

    return app
