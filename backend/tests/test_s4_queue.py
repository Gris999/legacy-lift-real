"""Real durable queue + worker tests (deterministic, no external AI)."""
from app import db, pipeline, migration_runs, workspace
from test_s3_baseline import ready_project
from test_flow import headers, client


def test_worker_is_separate_and_attempt_scoped(client,monkeypatch):
    pid=ready_project(client)
    summary,data=pipeline.perform(pid,'baseline')
    rid=db.run_create(pid,'baseline','demo');db.run_complete(rid,summary,data)
    response=client.post(f'/api/projects/{pid}/phases/modernize',headers=headers())
    assert response.status_code==200,response.text
    aid=response.json()['id']
    assert response.json()['status']=='queued'
    assert not workspace.project_candidate(pid).exists()
    assert client.post(f'/api/projects/{pid}/phases/modernize',headers=headers()).status_code==409
    attempt=migration_runs.run_one()
    assert attempt['status']=='completed',attempt
    frozen=migration_runs.candidate_path(pid,aid)
    assert frozen.is_dir()
    assert (frozen/'calculator.py').read_text().find('return x + 1')>0
    assert (workspace.project_source(pid)/'calculator.py').read_text().find('return (x + 1)')>0
    assert attempt['candidate_sha256']==workspace.snapshot_hash(frozen)
    assert len(migration_runs.history(pid))==1


def test_queue_enforces_new_human_action_for_retry(client):
    pid=ready_project(client)
    summary,data=pipeline.perform(pid,'baseline')
    rid=db.run_create(pid,'baseline','demo');db.run_complete(rid,summary,data)
    first=client.post(f'/api/projects/{pid}/phases/modernize',headers=headers()).json()
    assert migration_runs.run_one()['status']=='completed'
    retry=client.post(f"/api/projects/{pid}/migration/attempts/{first['id']}/retry",headers=headers())
    assert retry.status_code==202,retry.text
    assert retry.json()['parent_attempt_id']==first['id']
    assert len(migration_runs.history(pid))==2
