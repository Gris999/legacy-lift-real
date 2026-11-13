"""Password-authenticated, revocable SQLite sessions; the password is never a bearer token."""
from __future__ import annotations
import hashlib
import hmac
import os
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from . import db

ITERATIONS = 600_000
SESSION_HOURS = 12


def canonical_email(value: str) -> str:
    value = value.strip().lower()
    if len(value) > 320 or len(value) < 5 or '@' not in value or any(c.isspace() for c in value):
        raise ValueError('Correo electrónico inválido')
    return value


def password_hash(password: str) -> str:
    salt = os.urandom(24)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${hashed.hex()}'


def password_matches(password: str, encoded: str) -> bool:
    try:
        algo, rounds, salt, digest = encoded.split('$')
        if algo != 'pbkdf2_sha256' or not 300_000 <= int(rounds) <= 2_000_000:
            return False
        calculated = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(calculated, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False


def register(email: str, display_name: str, password: str, bootstrap_secret: str = '') -> dict:
    email = canonical_email(email)
    if len(password) < 12 or len(password) > 256:
        raise ValueError('La contraseña debe tener entre 12 y 256 caracteres')
    if not 2 <= len(display_name.strip()) <= 100:
        raise ValueError('Nombre inválido')
    hashed = password_hash(password)
    uid = str(uuid.uuid4())
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')  # only one first owner, even with concurrent registration
        count = c.execute('SELECT count(*) AS n FROM users').fetchone()['n']
        if not count:
            expected = os.getenv('LEGACYLIFT_BOOTSTRAP_SECRET', '')
            if len(expected) < 24 or expected.startswith('REPLACE_'):
                raise ValueError('Configura LEGACYLIFT_BOOTSTRAP_SECRET (24+ caracteres) en .env antes del primer registro')
            if not hmac.compare_digest(bootstrap_secret, expected):
                raise ValueError('Código de instalación incorrecto')
        if count and os.getenv('LEGACYLIFT_ALLOW_REGISTRATION', 'false').lower() != 'true':
            raise ValueError('El registro está cerrado por el administrador')
        try:
            c.execute('INSERT INTO users(id,email,display_name,password_hash,role,created_at) VALUES (?,?,?,?,?,?)',
                      (uid, email, display_name.strip(), hashed, 'owner' if not count else 'member', db.now()))
        except sqlite3.IntegrityError as exc:
            raise ValueError('El correo electrónico ya está registrado') from exc
        # A single-operator legacy installation has no owner_id. First account claims that data.
        if not count:
            c.execute('UPDATE projects SET owner_id=? WHERE owner_id IS NULL', (uid,))
    return user_get(uid)


def user_get(uid: str) -> dict | None:
    with db.connect() as c:
        row = c.execute('SELECT id,email,display_name,role,created_at FROM users WHERE id=? AND disabled_at IS NULL', (uid,)).fetchone()
        return dict(row) if row else None


def user_count() -> int:
    with db.connect() as c:
        return c.execute('SELECT count(*) AS n FROM users').fetchone()['n']


def _is_blocked(identity: str) -> bool:
    with db.connect() as c:
        row = c.execute('SELECT blocked_until FROM auth_attempts WHERE identity=?', (identity,)).fetchone()
        return bool(row and row['blocked_until'] and datetime.fromisoformat(row['blocked_until']) > datetime.now(timezone.utc))


def _failed(identity: str) -> None:
    with db.connect() as c:
        row = c.execute('SELECT attempts FROM auth_attempts WHERE identity=?', (identity,)).fetchone()
        n = (row['attempts'] if row else 0) + 1
        until = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat() if n >= 5 else None
        c.execute('INSERT INTO auth_attempts(identity,attempts,blocked_until) VALUES (?,?,?) ON CONFLICT(identity) DO UPDATE SET attempts=?,blocked_until=?',
                  (identity, n, until, n, until))


def _session(uid: str) -> dict:
    token = secrets.token_urlsafe(48)
    sid = str(uuid.uuid4())
    expiry = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    with db.connect() as c:
        c.execute('INSERT INTO auth_sessions(id,user_id,token_hash,created_at,expires_at) VALUES (?,?,?,?,?)',
                  (sid, uid, hashlib.sha256(token.encode()).hexdigest(), db.now(), expiry.isoformat()))
    return {'access_token': token, 'token_type': 'bearer', 'expires_at': expiry.isoformat()}


def login(email: str, password: str, peer: str = '') -> dict:
    try:
        email = canonical_email(email)
    except ValueError:
        raise HTTPException(401, 'Credenciales incorrectas')
    identity = hashlib.sha256((email + '|' + peer).encode()).hexdigest()
    if _is_blocked(identity):
        raise HTTPException(429, 'Demasiados intentos. Intenta después de 15 minutos')
    with db.connect() as c:
        row = c.execute('SELECT id,password_hash FROM users WHERE email=? AND disabled_at IS NULL', (email,)).fetchone()
    # Uniform expensive verification to avoid leaking whether an email exists.
    stored = row['password_hash'] if row else password_hash('dummy-verification-password')
    if not password_matches(password, stored) or not row:
        _failed(identity)
        raise HTTPException(401, 'Credenciales incorrectas')
    with db.connect() as c:
        c.execute('DELETE FROM auth_attempts WHERE identity=?', (identity,))
    return _session(row['id'])


def resolve(token: str) -> dict:
    if len(token) < 32 or len(token) > 256:
        raise HTTPException(401, 'Sesión inválida')
    digest = hashlib.sha256(token.encode()).hexdigest()
    with db.connect() as c:
        row = c.execute("""SELECT u.id,u.email,u.display_name,u.role,u.created_at
                           FROM auth_sessions s JOIN users u ON s.user_id=u.id
                           WHERE s.token_hash=? AND s.revoked_at IS NULL
                             AND s.expires_at>? AND u.disabled_at IS NULL""", (digest, db.now())).fetchone()
        if not row:
            raise HTTPException(401, 'Sesión inválida o expirada')
        return dict(row)


def revoke(token: str) -> None:
    digest = hashlib.sha256(token.encode()).hexdigest()
    with db.connect() as c:
        c.execute('UPDATE auth_sessions SET revoked_at=? WHERE token_hash=?', (db.now(), digest))
