import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app  # noqa: E402


@pytest.fixture()
def client():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    app.config.update(TESTING=True)
    with app.test_client() as client:
        with app.app_context():
            from app import db
            db.create_all()
        yield client


def test_gallery_page(client):
    r = client.get('/web/')
    assert r.status_code == 200
    # check a stable English token from template title
    assert b'WebImageDrive' in r.data


def test_upload_page(client):
    r = client.get('/web/upload')
    assert r.status_code == 200
    assert b'Upload' in r.data or b'WebImageDrive' in r.data