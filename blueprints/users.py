from flask import Blueprint, request
from utils.response import success
from utils.auth import jwt_required
from models import User

users_bp = Blueprint('users', __name__)


@users_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    uid = getattr(request, 'user_id', None)
    user = User.query.get(uid)
    return success({
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })
