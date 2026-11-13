"""Persistent asynchronous ingestion with retries and per-project serialization."""
from __future__ import annotations
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from . import db, ingestion

_executor=ThreadPoolExecutor(max_workers=2,thread_name_prefix='legacy-ingest')


def submit(pid: str, kind: str, params: dict, retry_of: str | None = None) -> dict:
    job=db.job_create(pid,kind,params,retry_of)
    _executor.submit(_process,pid,job['id'])
    return job


def _process(pid: str, jid: str) -> None:
    current=db.job_get(pid,jid)
    if not current or not db.job_claim(pid,jid):
        return
    input_data=current['input']
    kind=current['kind']
    try:
        if kind=='zip':
            input_path=Path(input_data['path'])
            if not input_path.is_file():
                raise ValueError('Archivo ZIP temporal no disponible; vuelve a subirlo')
            payload=input_path.read_bytes()
            db.job_update(pid,jid,'running','extracting',30)
            result=ingestion.ingest_zip(pid,payload,input_data['filename'])
        elif kind=='github':
            db.job_update(pid,jid,'running','cloning',25)
            result=ingestion.ingest_git(pid,input_data['user_id'],input_data['full_name'])
        else:
            raise ValueError('Tipo de operación no soportado')
        db.job_update(pid,jid,'running','indexing',90)
        db.job_update(pid,jid,'completed','completed',100,result=result)
        if kind=='zip':
            Path(input_data['path']).unlink(missing_ok=True)
    except Exception as exc:
        db.job_update(pid,jid,'failed','failed',0,error=str(exc))


def retry(pid: str,jid: str) -> dict:
    job=db.job_get(pid,jid)
    if not job or job['status'] not in {'failed','canceled'}:
        raise ValueError('Solo se pueden reintentar trabajos fallidos o cancelados')
    # Never reuse an OAuth token from the event; use the authenticated user's live connection.
    return submit(pid,job['kind'],job['input'],retry_of=jid)
