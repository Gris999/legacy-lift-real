"""Allowlisted, opt-in local Docker adapter for DEVELOPMENT only.

Production must use a separate ephemeral VM/worker with independently enforced limits.
No arbitrary repository scripts, package installers, Dockerfiles, network or privileged mounts.
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Protocol

class TestWorker(Protocol):
    def run_python_unittest(self, folder: Path) -> dict: ...

class DockerLocalWorker:
    def run_python_unittest(self, folder: Path) -> dict:
        if os.getenv('LEGACYLIFT_ENV','development').lower()!='development':
            return {'status':'not_run','reason':'Docker local prohibido fuera del entorno development'}
        if not shutil.which('docker'):
            return {'status':'not_run','reason':'Docker no está instalado'}
        # Image controlled only by the application operator, never by an uploaded repository.
        image=os.getenv('LEGACYLIFT_TEST_IMAGE','python:3.12-alpine')
        if not re.fullmatch(r'python:3\.(?:12|13)-(?:alpine|slim)(?:@sha256:[0-9a-f]{64})?',image):
            return {'status':'not_run','reason':'Imagen no autorizada por política local'}
        if not (folder/'tests').is_dir():
            return {'status':'not_run','reason':'No existe carpeta tests/ para unittest'}
        command=['docker','run','--rm','--pull','never','--network','none','--read-only',
            '--user','65534:65534','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--pids-limit','64','--memory','256m','--cpus','1','--ulimit','nofile=128:128',
            '--tmpfs','/tmp:rw,nosuid,nodev,noexec,size=32m','--env','PYTHONDONTWRITEBYTECODE=1',
            '--mount',f'type=bind,src={folder.resolve()},dst=/src,readonly',
            '--workdir','/src',image,'python','-m','unittest','discover','-s','tests','-v']
        try:
            proc=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
            output=proc.stdout+'\n'+proc.stderr
            count=re.search(r'Ran (\d+) tests?',output)
            if proc.returncode==125:
                return {'status':'not_run','reason':'Docker no pudo iniciar el contenedor; precarga la imagen autorizada (docker pull).'}
            if proc.returncode==0 and (not count or int(count.group(1))==0):
                return {'status':'not_run','reason':'La suite no produjo pruebas ejecutadas; no se declara éxito.'}
            return {'status':'passed' if proc.returncode==0 else 'failed','exit_code':proc.returncode,
                    'output':(proc.stdout+'\n'+proc.stderr)[-5000:],'worker':'docker-local-dev',
                    'image':image,'network':'none','read_only':True}
        except (OSError,subprocess.TimeoutExpired) as exc:
            return {'status':'not_run','reason':'Worker no disponible o excedió el tiempo: '+str(exc)[:120]}


def run_authorized(folder:Path, authorized:bool) -> dict:
    mode=os.getenv('LEGACYLIFT_WORKER_MODE','disabled').lower()
    if not authorized:
        return {'status':'not_run','reason':'Ejecución no autorizada para el snapshot/blueprint/wave actuales'}
    if mode!='docker-local':
        return {'status':'not_run','reason':'Worker de pruebas no habilitado. Solo se implementa docker-local en desarrollo.'}
    return DockerLocalWorker().run_python_unittest(folder)
