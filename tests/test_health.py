import os
import sys
import pytest

# Ensure project root is on path when tests run via conda run
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app  # noqa: E402


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_root_health(client):
    resp = client.get('/')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('status') == 'ok'