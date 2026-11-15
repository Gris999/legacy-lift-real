"""No uploaded code executes without snapshot-bound, human approval and an allowed worker."""
from app import baseline, db, execution, planning, pipeline, workspace
from test_flow import client, headers, sample_zip, await_ingest
import pytest


def ready_project(client):
    p=client.post('/api/projects',headers=headers(),json={'name':'Baseline S3', 'system_name':'Python','provider':'demo'}).json()
    pid=p['id']
    up=client.post(f'/api/projects/{pid}/upload',headers=headers(),files={'file':('code.zip',sample_zip(),'application/zip')})
    assert await_ingest(pid,up.json()['id'])['status']=='completed'
    for stage in ('discover','understand','assess','plan'):
        summary,details=pipeline.perform(pid,stage)
        rid=db.run_create(pid,stage,'demo');db.run_complete(rid,summary,details)
    plan=planning.current(pid)['data']
    plan['waves'][0]['strategy']='Refactor'
    assert client.patch(f'/api/projects/{pid}/blueprints/current',headers=headers(),json={'data':plan}).status_code==200
    assert client.post(f'/api/projects/{pid}/plan/decision',headers=headers(),json={'approved':True}).status_code==200
    assert client.post(f'/api/projects/{pid}/blueprints/current/waves/wave-01/decision',headers=headers(),json={'approved':True}).status_code==200
    return pid


def test_baseline_defaults_to_static_and_lists_tests(client,monkeypatch):
    pid=ready_project(client)
    monkeypatch.setenv('LEGACYLIFT_WORKER_MODE','docker-local')
    def must_not_run(*args,**kwargs):raise AssertionError('Unauthorized subprocess execution')
    monkeypatch.setattr(execution.subprocess,'run',must_not_run)
    before=client.get(f'/api/projects/{pid}/baseline/preflight',headers=headers()).json()
    assert before['ready'] and before['execution_authorized'] is False
    assert any('test_example.py' in t['path'] for t in before['tests'])
    summary,result=pipeline.perform(pid,'baseline')
    assert result['tests']['status']=='not_run'
    assert result['execution_authorized'] is False
    assert result['source_hash']==workspace.snapshot_hash(workspace.project_source(pid))
    assert result['blueprint_id']==planning.current(pid)['id']


def test_baseline_consent_scoped_and_revocation_invalidates(client,monkeypatch):
    pid=ready_project(client)
    monkeypatch.setenv('LEGACYLIFT_WORKER_MODE','disabled')
    response=client.post(f'/api/projects/{pid}/baseline/consent',headers=headers(),json={'approved':True})
    assert response.status_code==200,response.text
    assert baseline.authorized(pid)
    result=pipeline.perform(pid,'baseline')[1]
    assert result['tests']['status']=='not_run' # Worker remains disabled by operator.
    rid=db.run_create(pid,'baseline','demo');db.run_complete(rid,'baseline',result)
    response=client.post(f'/api/projects/{pid}/baseline/consent',headers=headers(),json={'approved':False})
    assert response.status_code==200,response.text
    assert baseline.authorized(pid) is False
    assert db.last_run(pid,'baseline')['status']=='superseded'
    # A changed Blueprint version never inherits the previous run authorization.
    edit=planning.current(pid)['data'].copy(); edit['title']='Nueva revisión'
    assert client.patch(f'/api/projects/{pid}/blueprints/current',headers=headers(),json={'data':edit}).status_code==200
    assert baseline.authorized(pid) is False


def test_test_proposals_require_review_and_do_not_run(client,monkeypatch):
    pid=ready_project(client)
    with db.connect() as conn:conn.execute("UPDATE projects SET provider='claude' WHERE id=?",(pid,))
    snapshot=db.project_get(pid)['active_snapshot_id']
    owner=db.project_get(pid)['owner_id']
    db.consent_set(pid,snapshot,'claude',owner,True)
    def fake_generate(*args,**kwargs):
        return '{"cases":[{"title":"Calcular total de la compra","input":"x=3","expected":"4","evidence_file":"calculator.py"}, {"title":"Inseguro","input":"1","expected":"2","evidence_file":"../outside.py"}]}'
    monkeypatch.setattr(baseline.ai,'generate',fake_generate)
    result=client.post(f'/api/projects/{pid}/baseline/suggestions',headers=headers())
    assert result.status_code==200,result.text
    rows=result.json()['proposals']
    assert len(rows)==1 and rows[0]['status']=='pending'
    assert client.post(f"/api/projects/{pid}/baseline/cases/{rows[0]['id']}/decision",headers=headers(),json={'approved':True}).status_code==200
    assert baseline.proposals(pid)[0]['status']=='approved'
    assert client.get(f'/api/projects/{pid}/baseline/preflight',headers=headers()).json()['proposals'][0]['status']=='approved'


def test_docker_worker_restrictions_without_starting_docker(client,monkeypatch):
    pid=ready_project(client)
    monkeypatch.setenv('LEGACYLIFT_ENV','production')
    monkeypatch.setenv('LEGACYLIFT_WORKER_MODE','docker-local')
    response=client.post(f'/api/projects/{pid}/baseline/consent',headers=headers(),json={'approved':True})
    assert response.status_code==200
    result=pipeline.perform(pid,'baseline')[1]
    assert result['tests']['status']=='not_run'
    assert 'fuera del entorno development' in result['tests']['reason']
    monkeypatch.setenv('LEGACYLIFT_ENV','development')
    monkeypatch.setenv('LEGACYLIFT_TEST_IMAGE','my-untrusted-image:latest')
    monkeypatch.setattr(execution.shutil,'which',lambda x:'/usr/bin/docker')
    result=pipeline.perform(pid,'baseline')[1]
    assert result['tests']['status']=='not_run'
    assert 'Imagen no autorizada' in result['tests']['reason']


def test_wave_reselection_invalidates_baseline_and_migration(client,monkeypatch):
    pid=ready_project(client)
    db.project_update(pid,migration_decision='approved')
    rid=db.run_create(pid,'baseline','demo')
    db.run_complete(rid,'captured',{'tests':{'status':'not_run'}})
    response=client.post(f'/api/projects/{pid}/blueprints/current/waves/wave-01/select',headers=headers())
    assert response.status_code==200,response.text
    assert db.last_run(pid,'baseline')['status']=='superseded'
    assert db.project_get(pid)['migration_decision'] is None
    assert baseline.authorized(pid) is False


def test_docker_zero_tests_cannot_be_marked_passed(monkeypatch,tmp_path):
    (tmp_path/'tests').mkdir()
    monkeypatch.setenv('LEGACYLIFT_ENV','development')
    monkeypatch.setenv('LEGACYLIFT_TEST_IMAGE','python:3.12-alpine')
    monkeypatch.setattr(execution.shutil,'which',lambda _: '/usr/bin/docker')
    class Result:
        returncode=0
        stdout='Ran 0 tests in 0.000s\n\nOK'
        stderr=''
    monkeypatch.setattr(execution.subprocess,'run',lambda *a,**kw:Result())
    assert execution.DockerLocalWorker().run_python_unittest(tmp_path)['status']=='not_run'
