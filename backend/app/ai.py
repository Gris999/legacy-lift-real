"""Provider adapters. Credentials never leave this server for the Angular client.

Codex uses the official locally-authenticated CLI (ChatGPT account).
Claude uses the official Anthropic Messages API and an independent API key.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import httpx


class AIError(RuntimeError):
    pass


def provider_status() -> list[dict]:
    return [
        {'id': 'codex', 'name': 'ChatGPT / Codex CLI', 'ready': shutil.which(os.getenv('CODEX_BIN', 'codex')) is not None,
         'help': 'Requiere codex login en la computadora anfitriona. El binario puede existir sin estar autenticado.'},
        {'id': 'claude', 'name': 'Claude / Anthropic API', 'ready': bool(os.getenv('CLAUDE_API_KEY')),
         'help': 'Requiere CLAUDE_API_KEY; la suscripción de Claude no sustituye la API key.'},
        {'id': 'demo', 'name': 'Demo determinista sin IA', 'ready': True,
         'help': 'Para probar la interfaz sin consumir tokens. Resultados explícitamente locales.'},
    ]


def codex_run(prompt: str, workspace: Path, edit: bool = False) -> str:
    cli = os.getenv('CODEX_BIN', 'codex')
    if shutil.which(cli) is None:
        raise AIError('Codex CLI no encontrado. Instala @openai/codex y ejecuta codex login en este PC.')
    cmd = [cli, 'exec', '--cd', str(workspace), '--sandbox', 'workspace-write' if edit else 'read-only',
           '--skip-git-repo-check', '-']
    try:
        result = subprocess.run(cmd, input=prompt, text=True, encoding='utf-8', errors='replace',
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=330, check=False)
    except subprocess.TimeoutExpired as exc:
        raise AIError('Codex excedió el límite de 330 segundos') from exc
    if result.returncode:
        raise AIError(f'Codex terminó con error: {result.stderr[-1000:] or result.stdout[-1000:]}')
    return (result.stdout or result.stderr)[-45000:]


def claude_run(prompt: str) -> str:
    token = os.getenv('CLAUDE_API_KEY', '')
    if not token:
        raise AIError('CLAUDE_API_KEY no configurada en el backend')
    try:
        response = httpx.post('https://api.anthropic.com/v1/messages',
            headers={'x-api-key':token, 'anthropic-version':'2023-06-01', 'content-type':'application/json'},
            json={'model':os.getenv('CLAUDE_MODEL', 'claude-sonnet-5'), 'max_tokens':6000,
                  'system':'Eres un ingeniero de software. Evita inventar evidencia, cambios no solicitados y afirmar validaciones no realizadas.',
                  'messages':[{'role':'user','content':prompt}]}, timeout=180)
        response.raise_for_status()
        return '\n'.join(x['text'] for x in response.json().get('content', []) if x.get('type') == 'text')
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise AIError(f'Error en la API de Claude: {str(exc)[:250]}') from exc


def generate(provider: str, prompt: str, workspace: Path, edit: bool = False) -> str:
    if provider == 'codex':
        return codex_run(prompt, workspace, edit=edit)
    if provider == 'claude':
        return claude_run(prompt)
    if provider == 'demo':
        raise AIError('El adaptador demo se ejecuta mediante las plantillas deterministas del pipeline')
    raise AIError('Proveedor no soportado')


def parse_edit_result(text: str) -> list[dict]:
    # Claude returns full replacement content for explicitly chosen files.
    candidate = text.strip()
    if candidate.startswith('```'):
        candidate = '\n'.join(candidate.splitlines()[1:-1]).strip()
    try:
        doc = json.loads(candidate)
        changes = doc['changes']
        if not isinstance(changes, list) or len(changes) > 5:
            raise ValueError('Máximo cinco cambios')
        for item in changes:
            if not isinstance(item.get('path'), str) or not isinstance(item.get('content'), str):
                raise ValueError('Formato de cambio inválido')
        return changes
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise AIError('Claude no devolvió un JSON de cambios válido. No se alteró el candidato.') from exc
