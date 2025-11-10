from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from models import Image
import os
import hashlib
from datetime import datetime

web_bp = Blueprint('web', __name__, url_prefix='/web')


def _compute_checksum(file_stream):
    sha256 = hashlib.sha256()
    for chunk in iter(lambda: file_stream.read(8192), b''):
        sha256.update(chunk)
    file_stream.seek(0)
    return sha256.hexdigest()


@web_bp.route('/')
def gallery():
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', 20)), 100)
    category = request.args.get('category')
    q = request.args.get('q')  # simple substring filter on filename for now

    query = Image.query
    if category:
        query = query.filter(Image.category == category)
    if q:
        like = f"%{q}%"
        query = query.filter(Image.filename.like(like))

    total = query.count()
    items = (query.order_by(Image.created_at.desc())
                  .offset((page - 1) * page_size)
                  .limit(page_size)
                  .all())

    return render_template('gallery.html', images=items, page=page, page_size=page_size, total=total, q=q, category=category)


@web_bp.route('/images/<int:image_id>')
def image_detail(image_id):
    img = Image.query.get_or_404(image_id)
    return render_template('detail.html', image=img)


@web_bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        category = request.form.get('category')
        tags = request.form.get('tags')
        if not f or not f.filename:
            flash('请选择文件', 'error')
            return redirect(request.url)
        filename = secure_filename(f.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        checksum = _compute_checksum(f.stream)
        existing = Image.query.filter_by(checksum=checksum).first()
        if existing:
            flash(f'文件已存在，引用 ID={existing.id}', 'info')
            return redirect(url_for('web.image_detail', image_id=existing.id))
        path = os.path.join(upload_folder, filename)
        f.save(path)
        size = os.path.getsize(path)
        img = Image(filename=filename, path=path, checksum=checksum, size=size, category=category, tags=tags, created_at=datetime.utcnow())
        db.session.add(img)
        db.session.commit()
        flash('上传成功', 'success')
        return redirect(url_for('web.image_detail', image_id=img.id))
    return render_template('upload.html')
