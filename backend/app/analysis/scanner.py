"""Static-first file analysis with explicit evidence and bounded reads.

The registry is deliberately simple: extensions, regex declarations and imports. Future
Tree-sitter/COBOL parsers can replace a strategy without changing the response contract.
"""
from __future__ import annotations

import ast
import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Language:
    name: str
    extensions: tuple[str, ...]
    declarations: tuple[tuple[str, str], ...] = ()
    dependencies: tuple[str, ...] = ()


LANGUAGES = (
    Language('Python', ('.py',), ((r'^\s*(?:async\s+)?def\s+(\w+)', 'function'), (r'^\s*class\s+(\w+)', 'class'))),
    Language('JavaScript', ('.js', '.jsx', '.mjs', '.cjs'), ((r'\b(?:class|function)\s+(\w+)', 'declaration'),),
             (r'(?:import\s+.*?from\s*|require\s*\()\s*[\'\"]([^\'\"]+)',)),
    Language('TypeScript', ('.ts', '.tsx', '.mts', '.cts'), ((r'\b(?:class|interface|type|function)\s+(\w+)', 'declaration'),),
             (r'(?:import\s+.*?from\s*|require\s*\()\s*[\'\"]([^\'\"]+)',)),
    Language('PHP', ('.php', '.phtml'), ((r'\b(?:class|interface|trait|function)\s+(\w+)', 'declaration'),),
             (r'\b(?:require|include)(?:_once)?\s*\(?\s*[\'\"]([^\'\"]+)', r'\buse\s+([\\\w]+)')),
    Language('Java', ('.java',), ((r'\b(?:class|interface|enum|record)\s+(\w+)', 'declaration'),), (r'^\s*import\s+([\w.*]+)\s*;',)),
    Language('COBOL', ('.cbl', '.cob', '.cobol', '.cpy', '.pco'),
             ((r'\bPROGRAM-ID\.\s*([\w-]+)', 'program'), (r'^\s*(?:\d{6}\s*)?([\w-]+)\s+SECTION\s*\.', 'section')),
             (r'\bCOPY\s+[\'\"]?([\w.-]+)', r'\bCALL\s+[\'\"]([\w-]+)')),
    Language('C#', ('.cs',)), Language('Go', ('.go',)), Language('SQL', ('.sql',)),
    Language('HTML', ('.html', '.htm')), Language('CSS', ('.css', '.scss')),
)
REGISTRY = {suffix: language for language in LANGUAGES for suffix in language.extensions}
MANIFESTS = {'package.json', 'composer.json', 'pom.xml', 'build.gradle', 'build.gradle.kts',
             'requirements.txt', 'pyproject.toml', 'go.mod', 'Gemfile', 'Cargo.toml'}
ENTRYPOINTS = {'main.py', 'main.ts', 'main.js', 'app.py', 'index.php', 'index.js', 'index.ts',
               'application.java', 'program.cs', 'package.json', 'pom.xml'}


def _node_id(module: str) -> str:
    return 'module:' + module


def _module(path: str) -> str:
    parts = Path(path).parts
    return parts[0] if len(parts) > 1 else '(raíz)'


def _file_symbols(text: str, language: Language, filename: str) -> tuple[list[dict], list[dict]]:
    declarations, dependencies = [], []
    if language.name == 'Python':
        try:
            tree = ast.parse(text, filename=filename)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    declarations.append({'name':node.name, 'kind':'class' if isinstance(node, ast.ClassDef) else 'function', 'line':node.lineno})
                elif isinstance(node, ast.Import):
                    dependencies.extend({'target':alias.name, 'line':node.lineno} for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    dependencies.append({'target':'.'*node.level+(node.module or ''), 'line':node.lineno})
        except SyntaxError:
            pass  # The syntax validator reports syntax failures separately.
    else:
        for line_no, line in enumerate(text.splitlines(), 1):
            # COBOL fixed format: columns 1-6 sequence, 7 indicator; skip comment lines.
            if language.name == 'COBOL' and len(line) > 6 and line[6] in {'*', '/'}:
                continue
            for regex, kind in language.declarations:
                for match in re.finditer(regex, line, re.I):
                    declarations.append({'name':match.group(1), 'kind':kind, 'line':line_no})
            for regex in language.dependencies:
                for match in re.finditer(regex, line, re.I):
                    dependencies.append({'target':match.group(1).rstrip('.'), 'line':line_no})
    return declarations[:80], dependencies[:120]


def scan(folder: Path, progress: Callable[[dict], None] | None = None) -> dict:
    files = sorted((f for f in folder.rglob('*') if f.is_file() and not f.is_symlink()),
                   key=lambda f: f.relative_to(folder).as_posix())
    total = len(files)
    code_bytes: Counter[str] = Counter()
    counts: Counter[str] = Counter()
    modules: Counter[str] = Counter()
    file_index: list[dict] = []
    findings: list[dict] = []
    symbols: list[dict] = []
    raw_deps: list[dict] = []
    manifests: list[str] = []
    test_files: list[str] = []
    entrypoints: list[str] = []
    total_lines = 0
    for idx, file in enumerate(files, 1):
        rel = file.relative_to(folder).as_posix()
        size = file.stat().st_size
        module = _module(rel)
        modules[module] += 1
        language = REGISTRY.get(file.suffix.lower())
        lang = language.name if language else 'Otro'
        counts[lang] += 1
        if language:
            code_bytes[lang] += size
        if file.name in MANIFESTS or file.suffix.lower() == '.csproj':
            manifests.append(rel)
        if file.name.lower() in ENTRYPOINTS or file.name.lower().endswith('application.java'):
            entrypoints.append(rel)
        if 'test' in file.name.lower() or 'spec' in file.name.lower():
            test_files.append(rel)
        item = {'path':rel, 'language':lang, 'module':module, 'bytes':size,
                'lines':0, 'selected':bool(language)}
        if language and size <= 5_000_000:
            content = file.read_text(encoding='utf-8-sig', errors='replace')
            lines = content.splitlines()
            item['lines'] = len(lines)
            total_lines += len(lines)
            decl, deps = _file_symbols(content[:1_000_000], language, rel)
            symbols.extend({**d, 'file':rel, 'language':lang} for d in decl[:40])
            raw_deps.extend({'file':rel, **d} for d in deps[:75])
            for line_no, line in enumerate(lines[:15000], 1):
                if re.search(r'\b(?:TODO|FIXME)\b', line, re.I):
                    rule='TODO_MARKER'
                    findings.append({'id':hashlib.sha256(f'{rel}:{line_no}:{rule}'.encode()).hexdigest()[:20],
                                     'file':rel, 'line':line_no, 'rule':rule, 'kind':'heuristic',
                                     'severity':'low', 'reason':'Marcador TODO/FIXME; requiere revisión',
                                     'evidence':{'file':rel,'line':line_no,'excerpt':line.strip()[:180]}})
                    if len(findings)>1500: break
        if size > 100_000 and lang != 'Otro':
            rule='LARGE_FILE'
            findings.append({'id':hashlib.sha256(f'{rel}:0:{rule}'.encode()).hexdigest()[:20],
                             'file':rel, 'line':None, 'rule':rule, 'kind':'heuristic', 'severity':'medium',
                             'reason':'Archivo de código grande; revisar responsabilidades',
                             'evidence':{'file':rel,'line':None,'excerpt':f'{size} bytes'}})
        file_index.append(item)
        if progress and (idx == 1 or idx == total or idx % max(1, min(25, total // 20)) == 0):
            progress({'scanned':idx, 'total':total,'percent':round(idx/max(total,1)*100),
                      'language_bytes':dict(code_bytes), 'languages':dict(counts)})
    # Only connect modules when a dependency target unambiguously names a local module.
    module_keys=set(modules)
    edges=set()
    deps_evidence=[]
    for dep in raw_deps:
        name=dep['target']
        target=name.removeprefix('./').removeprefix('../').split('/')[0].split('.')[0]
        origin=_module(dep['file'])
        local=target if target in module_keys else None
        if local and local != origin:
            edges.add((origin,local))
        deps_evidence.append({**dep,'module':origin, 'target_module':local,'resolved':bool(local)})
    total_code_bytes=sum(code_bytes.values())
    lang_breakdown=[{'name':lang,'bytes':size,'files':counts[lang],
                     'percent':round(size*100/total_code_bytes, 2) if total_code_bytes else 0}
                    for lang,size in code_bytes.most_common()]
    graph={'nodes':[{'id':_node_id(m),'label':m,'files':cnt,'kind':'module'} for m,cnt in modules.most_common(120)],
           'edges':[{'from':_node_id(a),'to':_node_id(b),'type':'DEPENDS_ON','inferred':False}
                    for a,b in sorted(edges)][:350],
           'note':'Dependencias locales inferidas por referencias estáticas; no refleja todas las llamadas dinámicas'}
    return {'schema_version':2,'files':total,'languages':dict(counts.most_common()),
            'language_bytes':dict(code_bytes),'language_breakdown':lang_breakdown,
            'total_code_bytes':total_code_bytes,'total_lines':total_lines,
            'modules':list(modules),'manifests':manifests,'findings':findings[:1500],
            'graph':graph,'test_files':test_files,'entrypoints':entrypoints,
            'symbols':symbols[:4000], 'dependencies':deps_evidence[:5000],
            'file_index':file_index,
            'methodology':'Porcentaje por bytes de extensiones reconocidas; no es GitHub Linguist ni ejecución de código.'}
