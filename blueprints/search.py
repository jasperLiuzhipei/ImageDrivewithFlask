from flask import Blueprint, request
from utils.response import success

search_bp = Blueprint('search', __name__)


@search_bp.route('/text', methods=['GET'])
def text_search():
    q = request.args.get('q', '')
    return success({'query': q, 'results': [], 'k': int(request.args.get('k', 10))})
