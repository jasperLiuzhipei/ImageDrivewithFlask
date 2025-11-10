import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext
from flask import current_app, request
from functools import wraps

from app import db
from models import User
from utils.response import error

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

_refresh_token_store: Dict[str, Dict[str, Any]] = {}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, role: str) -> str:
    exp_minutes = current_app.config.get("JWT_ACCESS_EXPIRES_MINUTES", 30)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "nonce": os.urandom(4).hex(),
        "exp": _now() + timedelta(minutes=exp_minutes),
        "iat": _now(),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=current_app.config["JWT_ALGORITHM"])


def create_refresh_token(user_id: int, role: str) -> str:
    exp_days = current_app.config.get("JWT_REFRESH_EXPIRES_DAYS", 7)
    jti = os.urandom(8).hex()
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "jti": jti,
        "nonce": os.urandom(4).hex(),
        "exp": _now() + timedelta(days=exp_days),
        "iat": _now(),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=current_app.config["JWT_ALGORITHM"])
    _refresh_token_store[jti] = {"user_id": user_id, "expires": _now() + timedelta(days=exp_days)}
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=[current_app.config["JWT_ALGORITHM"]])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def revoke_refresh_token(jti: str):
    _refresh_token_store.pop(jti, None)


def jwt_required(role: Optional[str] = None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return error(2001, "missing bearer token", status=401)
            token = auth_header.split(" ", 1)[1]
            payload = decode_token(token)
            if not payload or payload.get("type") != "access":
                return error(2002, "invalid or expired access token", status=401)
            if role and payload.get("role") != role:
                return error(2003, "insufficient role", status=403)
            try:
                request.user_id = int(payload.get("sub"))  # attach to request context
            except (TypeError, ValueError):
                return error(2002, "invalid token subject", status=401)
            request.user_role = payload.get("role")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_user_by_username(username: str) -> Optional[User]:
    return User.query.filter_by(username=username).first()


def create_user(username: str, password: str, role: str = "user") -> User:
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.session.add(user)
    db.session.commit()
    return user
