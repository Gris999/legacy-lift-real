"""Read-only, explicit source selection and bounded AI context batches."""
from __future__ import annotations
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from .scanner import REGISTRY
from .. import db, workspace


def indexed_files(pid: str, sid: str) -> list[dict]:
    discover=db.analysis_get(pid,sid,'discover') or {}
    return discover.get('file_index',[])


def selected_files(pid: str,sid: str) -> list[str]:
    index=indexed_files(pid,sid)
    allowed={x['path'] for x in index if x.get('selected') and Path(x['path']).suffix.lower() in REGISTRY}
    selection=db.selection_get(pid,sid)
    return sorted(allowed if selection is None else allowed.intersection(selection))


def context_batches(pid: str, folder: Path, max_batches: int | None = None) -> tuple[list[str],dict]:
    p=db.project_get(pid)
    sid=p.get('active_snapshot_id') if p else None
    if not sid: return [],{'files_selected':0,'files_included':0,'files_omitted':0,'batch_count':0}
    paths=selected_files(pid,sid)
    budget=max(4000,min(int(os.getenv('ANALYSIS_BATCH_CHARS','26000')),64000))
    configured_cap=max(1,min(int(os.getenv('ANALYSIS_MAX_AI_BATCHES','3')),12))
    batches_cap=min(configured_cap,max_batches) if max_batches else configured_cap
    batch=[];chunks=[];length=0;included=[]
    for rel in paths:
        file=folder/rel
        if not file.is_file() or file.is_symlink(): continue
        excerpt=file.read_text(encoding='utf-8-sig',errors='replace')[:min(7000,budget//2)]
        item=f'\n### ARCHIVO: {rel}\n```\n{excerpt}\n```\n'
        if length+len(item)>budget and batch:
            chunks.append(''.join(batch));batch=[];length=0
            if len(chunks)>=batches_cap:break
        if len(item)>budget: continue
        batch.append(item);length+=len(item);included.append(rel)
    if batch and len(chunks)<batches_cap:chunks.append(''.join(batch))
    return chunks,{'files_selected':len(paths),'files_included':len(included),
                   'files_omitted':len(paths)-len(included),'batch_count':len(chunks),
                   'selection_explicit':db.selection_get(pid,sid) is not None,
                   'budget_chars_per_batch':budget}


@contextmanager
def scoped_workspace(pid: str, source: Path):
    """Codex receives only the selected source tree as its cwd during analysis.

    This is defense-in-depth and does not substitute for OS-level confinement.
    """
    p=db.project_get(pid);sid=p.get('active_snapshot_id') if p else None
    with tempfile.TemporaryDirectory(prefix='legacylift-ai-') as temporary:
        destination=Path(temporary)
        if sid:
            for rel in selected_files(pid,sid):
                candidate=source/rel
                if not candidate.is_file() or candidate.is_symlink(): continue
                target=destination/rel
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(candidate,target)
                target.chmod(0o444)
        yield destination
