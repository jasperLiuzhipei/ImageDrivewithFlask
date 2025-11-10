from flask import Blueprint, request, current_app
import os
from werkzeug.utils import secure_filename
from utils.response import success, error

files_bp = Blueprint('files', __name__)


@files_bp.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return error(1001, 'no file provided')
    f = request.files['file']
    if not f.filename:
        return error(1002, 'empty filename')
    filename = secure_filename(f.filename)
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    f.save(file_path)
    return success({'filename': filename, 'path': file_path}, status=201)
