import os
from pathlib import Path

import pytest
from app import ai, workspace


def test_claude_changes_reject_invalid_json():
    with pytest.raises(ai.AIError):
        ai.parse_edit_result('I changed your files')


def test_zip_reject_sensitive_files():
    for name in ('../escape.py','/absolute.py','.env','key.pem','node_modules/package.json','C:/windows/system32'):
        with pytest.raises(ValueError):
            workspace.safe_relative(name)


def test_claude_changes_reject_tests(tmp_path, monkeypatch):
    from app import db, pipeline
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR', str(tmp_path))
    db.init()
    uid=__import__('app.auth',fromlist=['register']).register('security@example.test','Security','security-long-password-123','bootstrap-test-secret-with-32-plus-characters')['id']
    pid = db.project_create('Test', 'Python', 'claude',uid)['id']
    folder = workspace.project_candidate(pid)
    (folder / 'tests').mkdir(parents=True)
    (folder / 'tests' / 'test_a.py').write_text('assert True')
    with pytest.raises(ValueError, match='no permitido'):
        pipeline._apply_claude_changes(pid, '{"changes":[{"path":"tests/test_a.py","content":"assert False"}]}')
    assert (folder/'tests'/'test_a.py').read_text() == 'assert True'
