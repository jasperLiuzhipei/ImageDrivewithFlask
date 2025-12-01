from __future__ import annotations
import re
from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User
from app.utils.responses import ok, error
from app.utils.errors import AppError
import bcrypt

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not USERNAME_RE.match(username):
        return error("INVALID_USERNAME", "用户名不合法，需 3-32 位字母数字或下划线")
    if len(password) < 6:
        return error("WEAK_PASSWORD", "密码至少 6 位")
    if User.query.filter_by(username=username).first():
        return error("USERNAME_EXISTS", "用户名已存在")
    user = User(username=username, password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()
    return ok({"user_id": user.id, "username": user.username})


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return error("AUTH_FAILED", "用户名或密码错误", http=401)
    identity = str(user.id)
    access = create_access_token(identity=identity)
    refresh = create_refresh_token(identity=identity)
    return ok({"access_token": access, "refresh_token": refresh})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access = create_access_token(identity=user_id)
    return ok({"access_token": access})


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        raise AppError("USER_NOT_FOUND", "用户不存在", http=404)
    return ok({"user_id": user.id, "username": user.username})


@auth_bp.post("/change_password")
@jwt_required()
def change_password():
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    if len(new_password) < 6:
        return error("WEAK_PASSWORD", "新密码至少 6 位")
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error("USER_NOT_FOUND", "用户不存在", http=404)
    if not verify_password(old_password, user.password_hash):
        return error("BAD_OLD_PASSWORD", "原密码不正确", http=400)
    user.password_hash = hash_password(new_password)
    db.session.commit()
    return ok({"user_id": user.id, "username": user.username})

