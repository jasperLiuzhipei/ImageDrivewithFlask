from flask import Blueprint
from utils.response import success

images_bp = Blueprint('images', __name__)


@images_bp.route('/', methods=['GET'])
def list_images():
    return success({'items': [], 'meta': {'page': 1, 'page_size': 20, 'total': 0}})


@images_bp.route('/<int:image_id>', methods=['GET'])
def image_detail(image_id):
    return success({'id': image_id, 'metadata': {}})
