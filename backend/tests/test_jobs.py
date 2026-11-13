import io,time,zipfile
import pytest
from fastapi.testclient import TestClient
from app import db,workspace
from app.api import app

@pytest.fixture
def c(tmp_path,monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR',str(tmp_path))
    with TestClient(app) as client:
        reg=client.post('/api/auth/register',json={'email':'jobs@example.test','password':'very-long-password-321','display_name':'Jobs','bootstrap_secret':'bootstrap-test-secret-with-32-plus-characters'})
        headers={'Authorization':'Bearer '+reg.json()['access_token']}
        pid=client.post('/api/projects',headers=headers,json={'name':'Test Jobs','system_name':'Python','provider':'demo'}).json()['id']
        yield client,headers,pid

def sample_zip():
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,'w') as z:
        z.writestr('code.py','def hello():\n    return 1\n')
    return bio.getvalue()

def wait_job(pid,jid):
    for _ in range(150):
        job=db.job_get(pid,jid)
        if job['status'] not in ('queued','running'):
            return job
        time.sleep(.02)
    raise AssertionError('Job did not finish')

def test_async_ingest_events_and_snapshot(c):
    client,headers,pid=c
    r=client.post(f'/api/projects/{pid}/upload',headers=headers,files={'file':('repo.zip',sample_zip())})
    assert r.status_code==202,r.text
    job=wait_job(pid,r.json()['id'])
    assert job['status']=='completed',job
    assert job['result']['files']==1
    assert db.last_run(pid,'discover')['status']=='completed'
    assert db.events_after(pid,0)
    assert client.get(f'/api/projects/{pid}/jobs',headers=headers).json()[0]['status']=='completed'
    assert client.get(f'/api/projects/{pid}/jobs',headers={}).status_code==401

def test_failed_job_is_retriable_and_persistent(c):
    client,headers,pid=c
    r=client.post(f'/api/projects/{pid}/upload',headers=headers,files={'file':('broken.zip',b'not a zip')})
    job=wait_job(pid,r.json()['id'])
    assert job['status']=='failed'
    retry=client.post(f'/api/projects/{pid}/jobs/{job["id"]}/retry',headers=headers)
    assert retry.status_code==202,retry.text
    assert retry.json()['retry_of']==job['id']
    assert wait_job(pid,retry.json()['id'])['status']=='failed'
    assert len(db.jobs_list(pid))==2

def test_job_restart_marks_unfinished_as_failed(c):
    client,headers,pid=c
    with db.connect() as conn:
        import uuid
        conn.execute('INSERT INTO ingest_jobs(id,project_id,kind,input_json,status,stage,created_at) VALUES(?,?,?,?,?,?,?)',
          (str(uuid.uuid4()),pid,'zip','{}','running','acquiring',db.now()))
    db.init()
    assert db.jobs_list(pid)[0]['status']=='failed'


def test_block_phases_during_queued_job(c):
    client,headers,pid=c
    # Queueing is represented in SQLite so the test is deterministic.
    import uuid
    with db.connect() as conn:
        conn.execute('INSERT INTO ingest_jobs(id,project_id,kind,input_json,status,stage,created_at) VALUES(?,?,?,?,?,?,?)',
          (str(uuid.uuid4()),pid,'zip','{}','queued','queued',db.now()))
    r=client.post(f'/api/projects/{pid}/phases/discover',headers=headers)
    assert r.status_code==409
    assert 'ingesta' in r.text.lower() or 'importación' in r.text.lower()
    assert client.post(f'/api/projects/{pid}/plan/decision',headers=headers,json={'approved':True}).status_code==409
