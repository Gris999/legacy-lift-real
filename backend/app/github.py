"""GitHub OAuth App with PKCE, encrypted server-side tokens and allowlisted Git transport.

OAuth App `repo` scope covers private repos visible to the user, and is broad.
Never place the token in a URL, an Angular response, a logged command or the repository folder.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import re
import secrets
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException

from . import db

REPO_PATTERN = re.compile(r'^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$')


def configuration() -> dict:
    return {key: os.getenv(key, '').strip() for key in (
        'GITHUB_OAUTH_CLIENT_ID', 'GITHUB_OAUTH_CLIENT_SECRET', 'GITHUB_OAUTH_CALLBACK_URL',
        'GITHUB_OAUTH_RETURN_URL', 'LEGACYLIFT_ENCRYPTION_KEY')}


def ready() -> bool:
    return all(configuration().values())


def require_config() -> dict:
    config = configuration()
    if not all(config.values()):
        raise HTTPException(503, 'GitHub OAuth no configurado: revisa GITHUB_OAUTH_* y LEGACYLIFT_ENCRYPTION_KEY')
    if not (config['GITHUB_OAUTH_CALLBACK_URL'].startswith('https://') or config['GITHUB_OAUTH_CALLBACK_URL'].startswith('http://localhost:') or config['GITHUB_OAUTH_CALLBACK_URL'].startswith('http://127.0.0.1:')):
        raise HTTPException(503, 'El callback debe usar HTTPS, salvo localhost')
    try:
        Fernet(config['LEGACYLIFT_ENCRYPTION_KEY'].encode())
    except (ValueError, Exception) as exc:
        raise HTTPException(503, 'LEGACYLIFT_ENCRYPTION_KEY no es una clave Fernet válida') from exc
    return config


def http_client() -> httpx.Client:
    return httpx.Client(timeout=20, follow_redirects=False)


def start(uid: str) -> str:
    config = require_config()
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    expiry = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    with db.connect() as c:
        c.execute('INSERT INTO github_oauth_states(state_hash,user_id,code_verifier,expires_at) VALUES (?,?,?,?)',
                  (hashlib.sha256(state.encode()).hexdigest(), uid, verifier, expiry))
    params = {'client_id': config['GITHUB_OAUTH_CLIENT_ID'], 'redirect_uri': config['GITHUB_OAUTH_CALLBACK_URL'],
              'state': state, 'scope': 'repo', 'code_challenge': challenge, 'code_challenge_method':'S256'}
    return 'https://github.com/login/oauth/authorize?' + urlencode(params)


def complete(code: str, state: str) -> str:
    config = require_config()
    if not code or not state or len(state)>256 or len(code)>1000:
        raise HTTPException(400, 'Respuesta OAuth inválida')
    digest = hashlib.sha256(state.encode()).hexdigest()
    with db.connect() as c:
        row = c.execute('SELECT * FROM github_oauth_states WHERE state_hash=?', (digest,)).fetchone()
        # Single-use even if exchange fails; no replay.
        c.execute('DELETE FROM github_oauth_states WHERE state_hash=?', (digest,))
    if not row or datetime.fromisoformat(row['expires_at']) < datetime.now(timezone.utc):
        raise HTTPException(400, 'Estado OAuth caducado o no reconocido')
    with http_client() as http:
        response = http.post('https://github.com/login/oauth/access_token',
            data={'client_id':config['GITHUB_OAUTH_CLIENT_ID'], 'client_secret':config['GITHUB_OAUTH_CLIENT_SECRET'],
                  'code':code, 'redirect_uri':config['GITHUB_OAUTH_CALLBACK_URL'], 'code_verifier':row['code_verifier']},
            headers={'Accept':'application/json'})
        if response.status_code != 200:
            raise HTTPException(502, 'GitHub rechazó el intercambio OAuth')
        body=response.json()
        token=body.get('access_token')
        if not token or body.get('error'):
            raise HTTPException(502, 'GitHub no entregó un token de acceso')
        identity=http.get('https://api.github.com/user', headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token})
        if identity.status_code != 200:
            raise HTTPException(502, 'GitHub no permitió consultar la identidad')
        user=identity.json()
    if not isinstance(user.get('id'),int) or not user.get('login'):
        raise HTTPException(502, 'Identidad de GitHub incompleta')
    cipher=Fernet(config['LEGACYLIFT_ENCRYPTION_KEY'].encode())
    encrypted=cipher.encrypt(token.encode()).decode()
    with db.connect() as c:
        c.execute("""INSERT INTO github_connections(user_id,github_user_id,github_login,encrypted_token,connected_at)
                     VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
                     github_user_id=excluded.github_user_id,github_login=excluded.github_login,
                     encrypted_token=excluded.encrypted_token,connected_at=excluded.connected_at""",
                  (row['user_id'], str(user['id']), user['login'], encrypted, db.now()))
    return config['GITHUB_OAUTH_RETURN_URL']


def connection(uid: str) -> dict | None:
    with db.connect() as c:
        row=c.execute('SELECT github_login,github_user_id,connected_at FROM github_connections WHERE user_id=?', (uid,)).fetchone()
        return dict(row) if row else None


def _token(uid: str) -> str:
    config=require_config()
    with db.connect() as c:
        row=c.execute('SELECT encrypted_token FROM github_connections WHERE user_id=?', (uid,)).fetchone()
    if not row:
        raise HTTPException(409, 'Conecta tu cuenta de GitHub primero')
    return Fernet(config['LEGACYLIFT_ENCRYPTION_KEY'].encode()).decrypt(row['encrypted_token'].encode()).decode()


def disconnect(uid: str) -> None:
    with db.connect() as c:
        c.execute('DELETE FROM github_connections WHERE user_id=?', (uid,))


def repo_list(uid: str) -> list[dict]:
    token=_token(uid)
    output=[]
    with http_client() as http:
        for page in range(1,4):
            resp=http.get('https://api.github.com/user/repos',
                params={'per_page':100,'page':page,'sort':'updated','affiliation':'owner,collaborator,organization_member'},
                headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token})
            if resp.status_code != 200:
                raise HTTPException(502, 'No se pudieron listar los repositorios de GitHub')
            rows=resp.json()
            if not isinstance(rows, list):
                raise HTTPException(502, 'Respuesta de GitHub inesperada')
            for repo in rows:
                if repo.get('full_name') and REPO_PATTERN.fullmatch(repo['full_name']):
                    output.append({'full_name':repo['full_name'], 'private':bool(repo.get('private')),
                                   'default_branch':repo.get('default_branch') or 'main'})
            if len(rows)<100:
                break
    return output


def clone(uid: str, full_name: str, destination: Path) -> str:
    if not REPO_PATTERN.fullmatch(full_name) or full_name.startswith('.') or '/.' in full_name:
        raise ValueError('Repositorio inválido: usa owner/repo')
    token=_token(uid)
    with http_client() as http:
        resp=http.get('https://api.github.com/repos/'+full_name,
                      headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
        if resp.status_code != 200 or resp.json().get('full_name', '').lower() != full_name.lower():
            raise ValueError('Repositorio no disponible para tu cuenta de GitHub')
    # GitHub credentials are in a process environment variable, not URLs or argv.
    basic=base64.b64encode(('x-access-token:'+token).encode()).decode()
    env=dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1',
             GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
             GIT_CONFIG_VALUE_0='Authorization: Basic '+basic)
    try:
        subprocess.run(['git','-c','protocol.file.allow=never','clone','--depth','1',
                        '--no-tags','--','https://github.com/'+full_name+'.git',str(destination)],
                       env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,
                       text=True,timeout=120,check=True)
        result=subprocess.run(['git','-C',str(destination),'rev-parse','HEAD'],
                              stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                              check=True,text=True,timeout=10)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise ValueError('No se pudo clonar el repositorio: revisa permisos, acceso a GitHub y Git instalado') from exc
