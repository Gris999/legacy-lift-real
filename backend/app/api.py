from __future__ import annotations

import os
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import ai, auth as security, db, github, ingestion, jobs, pipeline, workspace
from .settings import cors_origins

@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init()
    ingestion.restore_legacy_snapshots()
    yield


app = FastAPI(title='LegacyLift API', version='0.1.0', docs_url=None, redoc_url=None, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=cors_origins(), allow_credentials=False,
                   allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Authorization', 'Content-Type'])


def current_user(authorization: str = Header(default='')) -> dict:
    if not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Se requiere una sesión')
    return security.resolve(authorization[7:].strip())



class Login(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1)


class Register(Login):
    bootstrap_secret: str = ""
    display_name: str = Field(min_length=2, max_length=100)



class NewProject(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    system_name: str = Field(min_length=2, max_length=80)
    provider: str = Field(pattern='^(codex|claude|demo)$')


def public_job(job: dict) -> dict:
    return {k:v for k,v in job.items() if k not in {'input_json','input','result_json'}}


class GitImport(BaseModel):
    full_name: str = Field(min_length=3,max_length=202)


class UpdateProject(BaseModel):
    name: str = Field(min_length=3, max_length=80)
    system_name: str = Field(min_length=2, max_length=80)


class Decision(BaseModel):
    approved: bool


@app.get('/api/health')
def health() -> dict:
    return {'ok':True, 'service':'legacylift'}


@app.get('/api/auth/config')
def auth_config() -> dict:
    return {'registration_open': security.user_count() == 0 or os.getenv('LEGACYLIFT_ALLOW_REGISTRATION', 'false').lower() == 'true', 'bootstrap_required':security.user_count()==0}


@app.post('/api/auth/register')
def register(data: Register) -> dict:
    try:
        user = security.register(data.email, data.display_name, data.password, data.bootstrap_secret)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {'user': user, **security.login(data.email, data.password)}


@app.post('/api/auth/login')
def login(data: Login, request: Request) -> dict:
    return security.login(data.email, data.password, request.client.host if request.client else '')


@app.post('/api/auth/logout')
def logout(authorization: str = Header(default=''), user: dict = Depends(current_user)) -> dict:
    security.revoke(authorization[7:].strip())
    return {'ok': True}


@app.get('/api/auth/me')
def me(user: dict = Depends(current_user)) -> dict:
    return {'username': user['display_name'], 'email': user['email'], 'role': user['role'], 'id':user['id']}


@app.get('/api/providers')
def providers(_user: dict = Depends(current_user)) -> list[dict]:
    return ai.provider_status()


@app.get('/api/projects')
def projects(user: dict = Depends(current_user)) -> list[dict]:
    return db.project_list(user['id'])


@app.post('/api/projects')
def create_project(data: NewProject, user: dict = Depends(current_user)) -> dict:
    return db.project_create(data.name, data.system_name, data.provider, user['id'])


def ensure_project(pid: str, user: dict) -> dict:
    p = db.project_get(pid, user['id'])
    if not p:
        raise HTTPException(404, 'Proyecto no encontrado')
    return p


@app.patch('/api/projects/{pid}')
def rename_project(pid: str, data: UpdateProject, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid, user)
    db.project_update(pid, name=data.name.strip(), system_name=data.system_name.strip())
    return ensure_project(pid, user)


@app.get('/api/github/status')
def github_status(user: dict = Depends(current_user)) -> dict:
    return {'configured': github.ready(), 'connection':github.connection(user['id'])}


@app.post('/api/github/connect')
def github_connect(user: dict = Depends(current_user)) -> dict:
    return {'url':github.start(user['id'])}


@app.get('/api/github/callback')
def github_callback(code: str = '', state: str = '') -> RedirectResponse:
    return RedirectResponse(github.complete(code,state), status_code=303)


@app.post('/api/github/disconnect')
def github_disconnect(user: dict = Depends(current_user)) -> dict:
    github.disconnect(user['id'])
    return {'ok':True}


@app.get('/api/github/repos')
def github_repos(user: dict = Depends(current_user)) -> list[dict]:
    return github.repo_list(user['id'])


@app.get('/api/projects/{pid}')
def get_project(pid: str, user: dict = Depends(current_user)) -> dict:
    p = ensure_project(pid, user)
    runs = db.runs_get(pid)
    return {**p, 'runs':runs, 'artifacts':workspace.artifacts(pid),
            'stages':list(pipeline.STAGES), 'phase_ready':{stage:pipeline.phase_ready(pid, stage)[0] for stage in pipeline.STAGES}}


@app.get('/api/projects/{pid}/snapshots')
def snapshots(pid: str, user: dict = Depends(current_user)) -> list[dict]:
    ensure_project(pid,user)
    return ingestion.list_snapshots(pid)


@app.post('/api/projects/{pid}/snapshots/{sid}/activate')
def activate_snapshot(pid: str, sid: str, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid,user)
    try:
        return ingestion.activate(pid,sid)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@app.post('/api/projects/{pid}/git',status_code=202)
def import_git(pid: str, data: GitImport, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid,user)
    if not github.connection(user['id']):
        raise HTTPException(409,'Conecta GitHub antes de importar')
    try:
        return public_job(jobs.submit(pid,'github',{'user_id':user['id'],'full_name':data.full_name}))
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@app.post('/api/projects/{pid}/upload',status_code=202)
async def upload(pid: str, file: UploadFile = File(...), user: dict = Depends(current_user)) -> dict:
    ensure_project(pid, user)
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(400, 'Sube un archivo .zip')
    raw = await file.read(workspace.MAX_ZIP_BYTES + 1)
    if len(raw)>workspace.MAX_ZIP_BYTES:
        raise HTTPException(413,'ZIP demasiado grande (máximo 12 MB)')
    # Save the payload for retries; never keep it in the HTTP request or in the event stream.
    upload_dir=workspace.root(pid)/'uploads'
    upload_dir.mkdir(parents=True,exist_ok=True)
    path=upload_dir/(str(uuid.uuid4())+'.zip')
    path.write_bytes(raw)
    path.chmod(0o600)
    try:
        return public_job(jobs.submit(pid,'zip',{'filename':Path(file.filename).name[:150],'path':str(path)}))
    except ValueError as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(409,str(exc)) from exc


@app.get('/api/projects/{pid}/jobs')
def list_jobs(pid: str, user: dict = Depends(current_user)) -> list[dict]:
    ensure_project(pid,user)
    return [public_job(j) for j in db.jobs_list(pid)]


@app.post('/api/projects/{pid}/jobs/{jid}/retry',status_code=202)
def retry_job(pid: str, jid: str, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid,user)
    try:
        return public_job(jobs.retry(pid,jid))
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@app.post('/api/projects/{pid}/jobs/{jid}/cancel')
def cancel_job(pid: str, jid: str, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid,user)
    if not db.job_get(pid,jid):
        raise HTTPException(404,'Trabajo no encontrado')
    if not db.job_cancel_queued(pid,jid):
        raise HTTPException(409,'Solo se puede cancelar un trabajo en cola')
    return {'ok':True}


@app.get('/api/projects/{pid}/events')
async def stream_events(pid: str, after: int = 0, user: dict = Depends(current_user)) -> StreamingResponse:
    ensure_project(pid,user)
    async def iterator():
        last=max(0,after)
        # Secure browser fetch() uses Authorization header; no bearer token in URL.
        yield ': connected\n\n'
        for _ in range(300):
            rows=db.events_after(pid,last)
            for entry in rows:
                last=entry['id']
                yield f"id: {last}\nevent: update\ndata: {json.dumps(entry,ensure_ascii=False)}\n\n"
            if not rows:
                yield ': ping\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(iterator(),media_type='text/event-stream',headers={
      'Cache-Control':'no-cache,no-transform','X-Accel-Buffering':'no'})


@app.post('/api/projects/{pid}/phases/{phase}')
def start_phase(pid: str, phase: str, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid, user)
    if any(j['status'] in ('queued', 'running') for j in db.jobs_list(pid)):
        raise HTTPException(409, 'La importación y el escaneo deben terminar antes de iniciar otras fases')
    try:
        return pipeline.start(pid, phase)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.post('/api/projects/{pid}/plan/decision')
def plan_decision(pid: str, body: Decision, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid, user)
    if any(j['status'] in ('queued', 'running') for j in db.jobs_list(pid)):
        raise HTTPException(409, 'Espera a que termine la ingesta antes de aprobar el plan')
    try:
        pipeline.decide_plan(pid, body.approved)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {'approved':body.approved}


@app.post('/api/projects/{pid}/migration/decision')
def migration_decision(pid: str, body: Decision, user: dict = Depends(current_user)) -> dict:
    ensure_project(pid, user)
    if any(j['status'] in ('queued', 'running') for j in db.jobs_list(pid)):
        raise HTTPException(409, 'Espera a que termine la ingesta antes de aprobar la migración')
    try:
        pipeline.decide_migration(pid, body.approved)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {'approved':body.approved}


@app.get('/api/projects/{pid}/artifacts/{filename}')
def get_artifact(pid: str, filename: str, user: dict = Depends(current_user)) -> Response:
    ensure_project(pid, user)
    if filename not in workspace.ARTIFACT_NAMES:
        raise HTTPException(404, 'Artefacto inexistente')
    path = workspace.artifact_dir(pid) / filename
    if not path.is_file():
        raise HTTPException(404, 'Artefacto no generado')
    return Response(path.read_text(encoding='utf-8'), media_type='text/plain; charset=utf-8')


@app.get('/api/projects/{pid}/export')
def export(pid: str, user: dict = Depends(current_user)) -> Response:
    project = ensure_project(pid, user)
    payload = workspace.export_zip(pid, project['migration_decision'] == 'approved')
    return Response(payload, media_type='application/zip',
                    headers={'Content-Disposition': 'attachment; filename="legacylift-evidencias.zip"'})
