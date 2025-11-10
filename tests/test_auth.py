import os
import sys
import pytest
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app  # noqa: E402


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        with app.app_context():
            from app import db
            db.create_all()
        yield client


def test_register_and_login_and_me_flow(client):
    # register
    r = client.post('/api/auth/register', json={"username": "alice", "password": "secret"})
    assert r.status_code == 201
    # duplicate register
    r2 = client.post('/api/auth/register', json={"username": "alice", "password": "secret"})
    assert r2.status_code == 409
    # login
    r3 = client.post('/api/auth/login', json={"username": "alice", "password": "secret"})
    assert r3.status_code == 200
    tokens = r3.get_json()["data"]
    access = tokens["access_token"]
    refresh = tokens["refresh_token"]
    # protected endpoint without token
    r4 = client.get('/api/users/me')
    assert r4.status_code == 401
    # protected with token
    r5 = client.get('/api/users/me', headers={"Authorization": f"Bearer {access}"})
    assert r5.status_code == 200
    me = r5.get_json()["data"]
    assert me["username"] == "alice"
    # refresh
    r6 = client.post('/api/auth/refresh', json={"refresh_token": refresh})
    assert r6.status_code == 200
    new_access = r6.get_json()["data"]["access_token"]
    assert new_access and new_access != access
    # logout (revoke refresh)
    r7 = client.post('/api/auth/logout', json={"refresh_token": refresh})
    assert r7.status_code == 200
    # refresh again should fail
    r8 = client.post('/api/auth/refresh', json={"refresh_token": refresh})
    assert r8.status_code == 401


def test_invalid_login(client):
    client.post('/api/auth/register', json={"username": "bob", "password": "pw"})
    bad = client.post('/api/auth/login', json={"username": "bob", "password": "wrong"})
    assert bad.status_code == 401
