from flask import Blueprint, request
from utils.response import success, error

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    if not data.get('username') or not data.get('password'):
        return error(1001, 'username and password required')
    # TODO: uniqueness check & persistence
    return success({"username": data['username']}, status=201)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    if not data.get('username') or not data.get('password'):
        return error(1001, 'username and password required')
    # TODO: validate credentials & issue tokens
    tokens = {"access_token": "stub-access", "refresh_token": "stub-refresh"}
    return success(tokens)
