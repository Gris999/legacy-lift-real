import io,time,zipfile
from fastapi.testclient import TestClient
from app import db,pipeline
from app.api import app


def test_assessment_scores_are_not_invented_and_reviews_are_stored(tmp_path,monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    with TestClient(app) as c:
        reg=c.post('/api/auth/register',json={'email':'assessment@test.test','password':'strong-password-123456','display_name':'Assessment','bootstrap_secret':'bootstrap-test-secret-with-32-plus-characters'})
        h={'Authorization':'Bearer '+reg.json()['access_token']}
        pid=c.post('/api/projects',headers=h,json={'name':'COBOL demo','system_name':'Payments','provider':'demo'}).json()['id']
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:z.writestr('account.cbl','       PROGRAM-ID. ACCOUNT.\n       *> TODO refine.\n')
        jid=c.post(f'/api/projects/{pid}/upload',headers=h,files={'file':('legacy.zip',b.getvalue())}).json()['id']
        for _ in range(200):
            if db.job_get(pid,jid)['status'] not in ('running','queued'):break
            time.sleep(.015)
        assert db.job_get(pid,jid)['status']=='completed'
        run_id=db.run_create(pid,'understand','demo')
        assert db.runs_get(pid)[-1]['snapshot_id']==db.project_get(pid)['active_snapshot_id']
        pipeline.perform(pid,'understand')
        db.run_complete(run_id,'Understood')
        result,details=pipeline.perform(pid,'assess')
        assert details['confidence_score'] is None
        assert details['metrics'][0]['value']==1
        assert details['signals']['heuristic_findings']>=1
        assert details['recommendations'][0]['strategy']=='Stabilize'
        assert 'sin score arbitrario' in result
        data=c.get(f'/api/projects/{pid}/analysis/assess',headers=h).json()['data']
        assert data['status']=='completed'
        assert any(r['phase']=='assess' for r in c.get(f'/api/projects/{pid}/analysis/reviews',headers=h).json())
