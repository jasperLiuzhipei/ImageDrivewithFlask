from flask import jsonify


def success(data=None, status=200):
    payload = {"success": True, "data": data, "error": None}
    return jsonify(payload), status


def error(code: int, message: str, status: int = 400, details=None):
    payload = {"success": False, "data": None, "error": {"code": code, "message": message, "details": details}}
    return jsonify(payload), status
