from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_env_file() -> None:
    """Load the repository's .env for local runs, without overriding real env vars."""
    path = ROOT / '.env'
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, value = line.split('=', 1)
        os.environ.setdefault(k.strip(), value.strip().strip('"').strip("'"))


load_env_file()


def data_dir() -> Path:
    raw = Path(os.getenv('LEGACYLIFT_DATA_DIR', str(ROOT / 'data')))
    return (ROOT / raw).resolve() if not raw.is_absolute() else raw.resolve()


def access_token() -> str:
    value = os.getenv('LEGACYLIFT_ACCESS_TOKEN', '')
    if len(value) < 24 or value.startswith('REPLACE_'):
        raise RuntimeError('Configura LEGACYLIFT_ACCESS_TOKEN con al menos 24 caracteres aleatorios en .env')
    return value


def cors_origins() -> list[str]:
    return [v.strip() for v in os.getenv('CORS_ORIGINS', 'http://localhost:4200').split(',') if v.strip()]
