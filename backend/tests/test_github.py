from urllib.parse import urlparse,parse_qs
import pytest
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
import httpx
from app.api import app
from app import github, db

class FakeClient:
    def __enter__(self):return self
    def __exit__(self,*args):return None
    def post(self,url,**kwargs):
        assert kwargs['data']['code_verifier']
        return httpx.Response(200,json={'access_token':'secret-oauth-token'})
    def get(self,url,**kwargs):
        if url.endswith('/user'):
            return httpx.Response(200,json={'id':123,'login':'sample'})
        if '/user/repos' in url:
            return httpx.Response(200,json=[{'full_name':'sample/private-repo','private':True,'default_branch':'main'}])
        return httpx.Response(200,json={'full_name':'sample/private-repo','private':True})

@pytest.fixture
def c(tmp_path,monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('GITHUB_OAUTH_CLIENT_ID','sample-id')
    monkeypatch.setenv('GITHUB_OAUTH_CLIENT_SECRET','sample-secret')
    monkeypatch.setenv('GITHUB_OAUTH_CALLBACK_URL','http://localhost:8000/api/github/callback')
    monkeypatch.setenv('GITHUB_OAUTH_RETURN_URL','http://localhost:4200/?github=connected')
    monkeypatch.setenv('LEGACYLIFT_ENCRYPTION_KEY',Fernet.generate_key().decode())
    monkeypatch.setattr(github,'http_client',FakeClient)
    with TestClient(app) as client:
        auth=client.post('/api/auth/register',json={'email':'github@example.test','password':'strong-github-password-123','display_name':'GitHub','bootstrap_secret':'bootstrap-test-secret-with-32-plus-characters'})
        yield client,{'Authorization':'Bearer '+auth.json()['access_token']}

def test_oauth_pkce_state_encrypted_token(c):
    client,h=c
    url=client.post('/api/github/connect',headers=h).json()['url']
    q=parse_qs(urlparse(url).query)
    assert q['code_challenge_method']==['S256']
    assert q['scope']==['repo']
    state=q['state'][0]
    r=client.get('/api/github/callback',params={'code':'abc','state':state},follow_redirects=False)
    assert r.status_code==303
    with db.connect() as conn:
        assert 'secret-oauth-token' not in conn.execute('SELECT encrypted_token FROM github_connections').fetchone()[0]
    assert client.get('/api/github/repos',headers=h).json()[0]['private'] is True
    assert client.get('/api/github/callback',params={'code':'abc','state':state}).status_code==400
    assert client.get('/api/github/callback',params={'code':'abc','state':'tampered'}).status_code==400
    assert client.post('/api/github/disconnect',headers=h).status_code==200
    assert client.get('/api/github/repos',headers=h).status_code==409

def test_unauthenticated_connection_denied(c):
    client,_=c
    assert client.post('/api/github/connect').status_code==401
    assert client.get('/api/github/repos').status_code==401
