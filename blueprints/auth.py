from flask import Blueprint, request
from utils.response import success, error
from utils.auth import (
    get_user_by_username,
    create_user,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_refresh_token,
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')
    if not username or not password:
        return error(1001, 'username and password required')
    if get_user_by_username(username):
        return error(1003, 'username already exists', status=409)
    user = create_user(username, password, role)
    return success({"id": user.id, "username": user.username, "role": user.role}, status=201)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return error(1001, 'username and password required')
    user = get_user_by_username(username)
    if not user or not verify_password(password, user.password_hash):
        return error(1004, 'invalid credentials', status=401)
    access = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id, user.role)
    return success({"access_token": access, "refresh_token": refresh})


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json() or {}
    token = data.get('refresh_token')
    if not token:
        return error(2004, 'missing refresh token', status=400)
    payload = decode_token(token)
    if not payload or payload.get('type') != 'refresh':
        return error(2005, 'invalid refresh token', status=401)
    # check if revoked
    jti = payload.get('jti')
    # simple revoked check handled by absence in store (not persisted yet)
    from utils.auth import _refresh_token_store  # local import for introspection
    if jti not in _refresh_token_store:
        return error(2006, 'refresh token revoked', status=401)
    access = create_access_token(payload['sub'], payload.get('role'))
    return success({"access_token": access})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    data = request.get_json() or {}
    token = data.get('refresh_token')
    if not token:
        return error(2004, 'missing refresh token', status=400)
    payload = decode_token(token)
    if not payload or payload.get('type') != 'refresh':
        return error(2005, 'invalid refresh token', status=401)
    revoke_refresh_token(payload.get('jti'))
    return success({"revoked": True})
