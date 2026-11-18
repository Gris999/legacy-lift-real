"""Sprint 5: tenant-aware access, team roles and project quotas on the existing SQLite store."""
from __future__ import annotations
import hashlib
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from . import db

ROLES = {'viewer': 1, 'developer': 2, 'admin': 3, 'owner': 4}
PLANS = {
    'starter': {'id':'starter','name':'Starter','max_projects':10,'max_members':3,'monthly_runs':100},
    'team': {'id':'team','name':'Team','max_projects':100,'max_members':25,'monthly_runs':1500},
    'enterprise': {'id':'enterprise','name':'Enterprise','max_projects':10000,'max_members':1000,'monthly_runs':100000},
}

def init() -> None:
    with db.connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS organizations (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, owner_id TEXT NOT NULL REFERENCES users(id),
            is_personal INTEGER NOT NULL DEFAULT 0, plan_id TEXT NOT NULL DEFAULT 'starter', created_at TEXT NOT NULL);
        CREATE UNIQUE INDEX IF NOT EXISTS one_personal_org ON organizations(owner_id) WHERE is_personal=1;
        CREATE TABLE IF NOT EXISTS organization_members (
            organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL CHECK(role IN ('owner','admin','developer','viewer')),
            joined_at TEXT NOT NULL, PRIMARY KEY(organization_id,user_id));
        CREATE TABLE IF NOT EXISTS organization_projects (
            project_id TEXT PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
            organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS organization_projects_org ON organization_projects(organization_id);
        CREATE TABLE IF NOT EXISTS organization_invitations (
            id TEXT PRIMARY KEY, organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            email TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','developer','viewer')),
            token_hash TEXT NOT NULL UNIQUE, created_by TEXT NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL, expires_at TEXT NOT NULL, accepted_at TEXT);
        CREATE TABLE IF NOT EXISTS organization_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            user_id TEXT REFERENCES users(id), action TEXT NOT NULL, resource TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS organization_audit_org ON organization_audit(organization_id,id);
        """)

def personal(uid: str) -> str:
    """Idempotent workspace + migration for legacy owner-only projects."""
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT id FROM organizations WHERE owner_id=? AND is_personal=1',(uid,)).fetchone()
        if row:
            oid=row['id']
        else:
            oid=str(uuid.uuid4())
            c.execute('INSERT INTO organizations(id,name,owner_id,is_personal,created_at) VALUES(?,?,?,?,?)',
                      (oid,'Espacio personal',uid,1,db.now()))
        c.execute('INSERT OR IGNORE INTO organization_members(organization_id,user_id,role,joined_at) VALUES(?,?,?,?)',
                  (oid,uid,'owner',db.now()))
        c.execute("""INSERT OR IGNORE INTO organization_projects(project_id,organization_id)
            SELECT p.id,? FROM projects p WHERE p.owner_id=?
            AND NOT EXISTS(SELECT 1 FROM organization_projects op WHERE op.project_id=p.id)""",(oid,uid))
    return oid

def organization(oid:str,uid:str,minimum:str='viewer') -> dict:
    with db.connect() as c:
        row=c.execute("""SELECT o.*,m.role FROM organizations o JOIN organization_members m
            ON m.organization_id=o.id WHERE o.id=? AND m.user_id=?""",(oid,uid)).fetchone()
    if not row: raise HTTPException(404,'Organización no encontrada')
    if ROLES[row['role']] < ROLES[minimum]:
        raise HTTPException(403,'No tienes permisos para esta acción')
    return dict(row)

def list_organizations(uid:str) -> list[dict]:
    personal(uid)
    with db.connect() as c:
        return [dict(r) for r in c.execute("""SELECT o.id,o.name,o.is_personal,o.plan_id,m.role,
          (SELECT COUNT(*) FROM organization_projects WHERE organization_id=o.id) AS project_count,
          (SELECT COUNT(*) FROM organization_members WHERE organization_id=o.id) AS member_count
          FROM organizations o JOIN organization_members m ON m.organization_id=o.id
          WHERE m.user_id=? ORDER BY o.is_personal DESC,o.created_at""",(uid,))]

def _audit(c:sqlite3.Connection,oid:str,uid:str,action:str,resource:str) -> None:
    c.execute('INSERT INTO organization_audit(organization_id,user_id,action,resource,created_at) VALUES(?,?,?,?,?)',
              (oid,uid,action,resource,db.now()))

def create_organization(uid:str,name:str) -> dict:
    if not 3<=len(name.strip())<=80: raise HTTPException(422,'Nombre de organización inválido')
    oid=str(uuid.uuid4())
    with db.connect() as c:
        c.execute('INSERT INTO organizations(id,name,owner_id,created_at) VALUES(?,?,?,?)',(oid,name.strip(),uid,db.now()))
        c.execute('INSERT INTO organization_members(organization_id,user_id,role,joined_at) VALUES(?,?,?,?)',
                  (oid,uid,'owner',db.now()))
        _audit(c,oid,uid,'organization.created','organization')
    return organization(oid,uid)

def project_list(uid:str) -> list[dict]:
    personal(uid)
    with db.connect() as c:
        return [dict(r) for r in c.execute("""SELECT p.*,op.organization_id,m.role AS organization_role
            FROM projects p JOIN organization_projects op ON op.project_id=p.id
            JOIN organization_members m ON m.organization_id=op.organization_id
            WHERE m.user_id=? ORDER BY p.created_at DESC""",(uid,))]

def project_access(pid:str,uid:str,minimum:str='viewer') -> dict:
    personal(uid)
    with db.connect() as c:
        row=c.execute("""SELECT p.*,op.organization_id,m.role AS organization_role
            FROM projects p JOIN organization_projects op ON op.project_id=p.id
            JOIN organization_members m ON m.organization_id=op.organization_id
            WHERE p.id=? AND m.user_id=?""",(pid,uid)).fetchone()
    if not row: raise HTTPException(404,'Proyecto no encontrado')
    if ROLES[row['organization_role']]<ROLES[minimum]:
        raise HTTPException(403,'Tu rol no permite modificar este proyecto')
    return dict(row)

def create_project(uid:str,oid:str,name:str,system:str,provider:str) -> dict:
    organization(oid,uid,'developer')
    pid=str(uuid.uuid4())
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        member=c.execute('SELECT role FROM organization_members WHERE organization_id=? AND user_id=?',(oid,uid)).fetchone()
        if not member or ROLES[member['role']]<ROLES['developer']:
            raise HTTPException(403,'Tu rol no permite crear proyectos')
        org=c.execute('SELECT plan_id FROM organizations WHERE id=?',(oid,)).fetchone()
        count=c.execute('SELECT COUNT(*) AS n FROM organization_projects WHERE organization_id=?',(oid,)).fetchone()['n']
        if count>=PLANS[org['plan_id']]['max_projects']:
            raise HTTPException(409,'Límite de proyectos de tu plan alcanzado')
        c.execute('INSERT INTO projects(id,name,system_name,provider,created_at,owner_id) VALUES(?,?,?,?,?,?)',
                  (pid,name,system,provider,db.now(),uid))
        c.execute('INSERT INTO organization_projects(project_id,organization_id) VALUES(?,?)',(pid,oid))
        _audit(c,oid,uid,'project.created','project:'+pid)
    return project_access(pid,uid)

def members(oid:str,uid:str) -> list[dict]:
    organization(oid,uid,'admin')
    with db.connect() as c:
        return [dict(r) for r in c.execute("""SELECT u.id,u.email,u.display_name,m.role,m.joined_at
            FROM organization_members m JOIN users u ON u.id=m.user_id
            WHERE m.organization_id=? ORDER BY m.joined_at""",(oid,))]

def invite(oid:str,uid:str,email:str,role:str) -> dict:
    from .auth import canonical_email
    organization(oid,uid,'admin')
    if role not in ('admin','developer','viewer'): raise HTTPException(422,'Rol inválido')
    try: email=canonical_email(email)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    token=secrets.token_urlsafe(32)
    expires=(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        existing=c.execute("""SELECT 1 FROM users u JOIN organization_members m ON m.user_id=u.id
             WHERE m.organization_id=? AND u.email=?""",(oid,email)).fetchone()
        if existing: raise HTTPException(409,'Este usuario ya pertenece a la organización')
        c.execute("""INSERT INTO organization_invitations(id,organization_id,email,role,token_hash,created_by,
            created_at,expires_at) VALUES(?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()),oid,email,role,hashlib.sha256(token.encode()).hexdigest(),uid,db.now(),expires))
        _audit(c,oid,uid,'member.invited','member')
    return {'token':token,'email':email,'role':role,'expires_at':expires,
            'note':'Comparte este código por un canal privado; se muestra una sola vez. El invitado necesita una cuenta.'}

def accept_invitation(uid:str,token:str) -> dict:
    if not 20<=len(token)<=128: raise HTTPException(400,'Invitación inválida')
    digest=hashlib.sha256(token.encode()).hexdigest()
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute("""SELECT i.*,u.email AS account_email FROM organization_invitations i
            JOIN users u ON u.id=? WHERE i.token_hash=? AND i.accepted_at IS NULL AND i.expires_at>?""",
            (uid,digest,db.now())).fetchone()
        if not row or row['email']!=row['account_email']:
            raise HTTPException(400,'Invitación inválida, expirada o asignada a otro correo')
        oid=row['organization_id']
        plan=c.execute('SELECT plan_id FROM organizations WHERE id=?',(oid,)).fetchone()['plan_id']
        count=c.execute('SELECT COUNT(*) AS n FROM organization_members WHERE organization_id=?',(oid,)).fetchone()['n']
        if count>=PLANS[plan]['max_members']:
            raise HTTPException(409,'Límite de integrantes alcanzado')
        c.execute('INSERT OR IGNORE INTO organization_members(organization_id,user_id,role,joined_at) VALUES(?,?,?,?)',
                  (oid,uid,row['role'],db.now()))
        c.execute('UPDATE organization_invitations SET accepted_at=? WHERE id=?',(db.now(),row['id']))
        _audit(c,oid,uid,'member.joined','member')
    return organization(oid,uid)

def update_member(oid:str,uid:str,target:str,role:str|None) -> dict:
    org=organization(oid,uid,'admin')
    if target==org['owner_id']: raise HTTPException(403,'El propietario no puede ser eliminado ni degradado')
    if role not in (None,'admin','developer','viewer'): raise HTTPException(422,'Rol inválido')
    if role=='admin' and org['role']!='owner':
        raise HTTPException(403,'Solo el propietario puede nombrar administradores')
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        existing=c.execute('SELECT role FROM organization_members WHERE organization_id=? AND user_id=?',(oid,target)).fetchone()
        if not existing: raise HTTPException(404,'Miembro no encontrado')
        if existing['role']=='admin' and org['role']!='owner':
            raise HTTPException(403,'Solo el propietario puede cambiar a un administrador')
        if role is None:
            c.execute('DELETE FROM organization_members WHERE organization_id=? AND user_id=?',(oid,target))
        else:
            c.execute('UPDATE organization_members SET role=? WHERE organization_id=? AND user_id=?',(role,oid,target))
        _audit(c,oid,uid,'member.removed' if role is None else 'member.role_changed','member:'+target)
    return {'ok':True}

def record_action(uid:str,method:str,route:str,pid:str='',oid:str='') -> None:
    """Log only successful route templates, never headers, payloads, tokens or source."""
    if not (route.startswith('/api/projects') or route.startswith('/api/organizations')): return
    with db.connect() as c:
        if pid:
            link=c.execute('SELECT organization_id FROM organization_projects WHERE project_id=?',(pid,)).fetchone()
            oid=link['organization_id'] if link else ''
        if oid: _audit(c,oid,uid,method.lower()+' '+route,'project:'+pid if pid else 'organization')

def audit_log(oid:str,uid:str,limit:int=100) -> list[dict]:
    organization(oid,uid,'admin')
    with db.connect() as c:
        return [dict(r) for r in c.execute("""SELECT a.id,a.user_id,u.display_name,a.action,a.resource,a.created_at
            FROM organization_audit a LEFT JOIN users u ON u.id=a.user_id
            WHERE a.organization_id=? ORDER BY a.id DESC LIMIT ?""",(oid,min(200,max(1,limit))))]

def check_run_quota(pid:str,uid:str) -> None:
    project=project_access(pid,uid,'developer')
    oid=project['organization_id']
    with db.connect() as c:
        plan=c.execute('SELECT plan_id FROM organizations WHERE id=?',(oid,)).fetchone()['plan_id']
        period=db.now()[:7]
        count=c.execute("""SELECT COUNT(*) AS n FROM phase_runs r
            JOIN organization_projects op ON op.project_id=r.project_id
            WHERE op.organization_id=? AND substr(r.started_at,1,7)=?""",(oid,period)).fetchone()['n']
        if count>=PLANS[plan]['monthly_runs']:
            raise HTTPException(409,'Cuota mensual de ejecuciones alcanzada')
