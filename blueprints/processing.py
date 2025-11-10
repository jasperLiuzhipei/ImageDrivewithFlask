from flask import Blueprint, request
from utils.response import success, error

processing_bp = Blueprint('processing', __name__)


@processing_bp.route('/trigger', methods=['POST'])
def trigger_processing():
    data = request.get_json() or {}
    if 'image_id' not in data:
        return error(1001, 'image_id required')
    tasks = data.get('tasks', ['embedding', 'ocr'])
    return success({'image_id': data['image_id'], 'queued_tasks': tasks}, status=202)
