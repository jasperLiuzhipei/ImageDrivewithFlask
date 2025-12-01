"""Unified JSON response helpers (draft)."""
from __future__ import annotations
from flask import jsonify


def ok(data: dict | list | None = None, **extra):
    payload = {"status": "ok"}
    if data is not None:
        payload["data"] = data
    if extra:
        payload.update(extra)
    return jsonify(payload), 200


def error(code: str, message: str, details: dict | list | str | None = None, http=400, trace_id: str | None = None):
    payload = {
        "status": "error",
        "code": code,
        "message": message,
    }
    if details is not None:
        payload["details"] = details
    if trace_id is not None:
        payload["trace_id"] = trace_id
    return jsonify(payload), http
