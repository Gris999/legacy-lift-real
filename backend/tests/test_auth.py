import pytest
from fastapi.testclient import TestClient
from app import db
from app.api import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR', str(tmp_path))
    monkeypatch.setenv('LEGACYLIFT_ALLOW_REGISTRATION','true')
    with TestClient(app) as c:
        yield c

def register(client,email):
    return client.post('/api/auth/register',json={'email':email,'password':'correct-long-password-123','display_name':'Prueba','bootstrap_secret':'bootstrap-test-secret-with-32-plus-characters'})

def test_passwords_sessions_expiration_and_revocation(client):
    a=register(client,'one@example.test')
    assert a.status_code==200,a.text
    token=a.json()['access_token']
    assert token != 'correct-long-password-123'
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==200
    with db.connect() as c:
        assert 'correct-long-password' not in c.execute('SELECT password_hash FROM users').fetchone()['password_hash']
    assert client.post('/api/auth/logout',headers={'Authorization':'Bearer '+token}).status_code==200
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+token}).status_code==401
    b=client.post('/api/auth/login',json={'email':'one@example.test','password':'correct-long-password-123'})
    t=b.json()['access_token']
    assert t!=token
    with db.connect() as c:
        c.execute("UPDATE auth_sessions SET expires_at='2001-01-01T00:00:00+00:00' WHERE token_hash=?",(__import__('hashlib').sha256(t.encode()).hexdigest(),))
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+t}).status_code==401

def test_project_isolation(client):
    a=register(client,'first@example.test').json()['access_token']
    b=register(client,'second@example.test').json()['access_token']
    ah={'Authorization':'Bearer '+a}; bh={'Authorization':'Bearer '+b}
    pid=client.post('/api/projects',headers=ah,json={'name':'Project A','system_name':'Python','provider':'demo'}).json()['id']
    assert len(client.get('/api/projects',headers=bh).json())==0
    assert client.get(f'/api/projects/{pid}',headers=bh).status_code==404
    assert client.post(f'/api/projects/{pid}/phases/discover',headers=bh).status_code==404
    assert client.get(f'/api/projects/{pid}/export',headers=bh).status_code==404


def test_bootstrap_secret_and_registration_closed(client,monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_ALLOW_REGISTRATION','false')
    wrong=client.post('/api/auth/register',json={
        'email':'bootstrap@example.test','password':'secure-password-123','display_name':'Owner','bootstrap_secret':'wrong'})
    assert wrong.status_code==400
    first=register(client,'owner@example.test')
    assert first.status_code==200,first.text
    assert first.json()['user']['role']=='owner'
    second=register(client,'uninvited@example.test')
    assert second.status_code==400
