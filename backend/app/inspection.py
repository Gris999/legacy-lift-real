from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

EXTENSIONS = {'.py': 'Python', '.ts': 'TypeScript', '.tsx': 'TypeScript', '.js': 'JavaScript',
              '.jsx': 'JavaScript', '.java': 'Java', '.cs': 'C#', '.go': 'Go',
              '.php': 'PHP', '.sql': 'SQL', '.html': 'HTML', '.css': 'CSS'}
MANIFESTS = ('pyproject.toml', 'requirements.txt', 'package.json', 'pom.xml', 'build.gradle', 'build.gradle.kts', 'go.mod', '*.csproj')


def inspect(folder: Path) -> dict:
    files = [f for f in folder.rglob('*') if f.is_file() and not f.is_symlink()]
    languages = Counter(EXTENSIONS.get(f.suffix.lower(), 'Otro') for f in files)
    modules = sorted({f.relative_to(folder).parts[0] for f in files})[:100]
    manifests = [f.relative_to(folder).as_posix() for f in files if f.name in MANIFESTS or f.suffix == '.csproj']
    findings = []
    edges = []
    for file in files:
        rel = file.relative_to(folder).as_posix()
        if file.stat().st_size > 100_000:
            findings.append({'file': rel, 'severity': 'medium', 'reason': 'Archivo muy grande: revisar modularidad', 'kind': 'heuristic'})
        if file.suffix.lower() not in {'.py', '.js', '.ts', '.java', '.cs', '.go'}:
            continue
        text = file.read_text(encoding='utf-8', errors='replace')[:120_000]
        if 'TODO' in text or 'FIXME' in text:
            findings.append({'file': rel, 'severity': 'low', 'reason': 'Marcador TODO/FIXME; requiere revisión', 'kind': 'heuristic'})
        for match in re.findall(r'^\s*(?:from|import|require\()\s*[\"\']?([\w./-]+)', text, re.M)[:35]:
            edges.append({'from': rel, 'to': match, 'type': 'DEPENDS_ON', 'inferred': True})
    return {'files': len(files), 'languages': dict(languages.most_common()), 'modules': modules,
            'manifests': manifests, 'findings': findings[:70], 'graph': {'nodes': modules, 'edges': edges[:200]},
            'test_files': [f.relative_to(folder).as_posix() for f in files if 'test' in f.name.lower()][:60]}


def inventory_md(data: dict) -> str:
    return ('# Discover — Inventario técnico\n\n'
            f"Archivos: **{data['files']}**.\n\n"
            '## Tecnologías\n' + ''.join(f'- {k}: {v} archivos\n' for k,v in data['languages'].items()) +
            '\n## Módulos\n' + ''.join(f'- `{v}`\n' for v in data['modules']) +
            '\n## Manifiestos\n' + ''.join(f'- `{v}`\n' for v in data['manifests']) +
            '\n## Hallazgos heurísticos (no son vulnerabilidades confirmadas)\n' +
            (''.join(f"- **{x['severity']}** `{x['file']}`: {x['reason']}\n" for x in data['findings']) or '- Ninguno observado.\n'))


def static_checks(folder: Path) -> list[dict]:
    checks = []
    for file in sorted(folder.rglob('*')):
        if not file.is_file() or file.is_symlink():
            continue
        rel = file.relative_to(folder).as_posix()
        try:
            if file.suffix.lower() == '.py':
                ast.parse(file.read_text(encoding='utf-8-sig'), filename=rel)
            elif file.suffix.lower() == '.json':
                json.loads(file.read_text(encoding='utf-8-sig'))
            else:
                continue
            checks.append({'file':rel, 'status':'passed', 'check':'syntax'})
        except (SyntaxError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            checks.append({'file': rel, 'status':'failed', 'check':'syntax', 'error':str(exc)[:240]})
    return checks


def check_summary(checks: list[dict]) -> dict:
    return {'total':len(checks), 'passed':sum(x['status']=='passed' for x in checks),
            'failed':sum(x['status']=='failed' for x in checks)}
