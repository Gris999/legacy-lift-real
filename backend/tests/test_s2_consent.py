import io,time,zipfile
from fastapi.testclient import TestClient
from app.api import app
from app import db,pipeline


def test_consent_is_per_snapshot_and_review_is_user_owned(tmp_path,monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    with TestClient(app) as c:
        reg=c.post('/api/auth/register',json={'email':'s2@example.test','display_name':'S2 Test','password':'testing-long-password-123','bootstrap_secret':'bootstrap-test-secret-with-32-plus-characters'})
        h={'Authorization':'Bearer '+reg.json()['access_token']}
        p=c.post('/api/projects',headers=h,json={'name':'Proyecto privado','system_name':'COBOL','provider':'codex'}).json();pid=p['id']
        blob=io.BytesIO()
        with zipfile.ZipFile(blob,'w') as z:z.writestr('book.cbl','       PROGRAM-ID. BOOK.\n       COPY CUSTOMER.\n       *> TODO revise.\n')
        up=c.post(f'/api/projects/{pid}/upload',headers=h,files={'file':('src.zip',blob.getvalue())})
        jid=up.json()['id']
        for _ in range(200):
            job=db.job_get(pid,jid)
            if job['status'] not in ('queued','running'):break
            time.sleep(.015)
        assert job['status']=='completed',job
        assert c.get(f'/api/projects/{pid}/analysis/consent',headers=h).json()['approved'] is False
        assert c.post(f'/api/projects/{pid}/phases/understand',headers=h).status_code==409
        assert c.post(f'/api/projects/{pid}/analysis/consent',headers=h,json={'approved':True}).json()['approved']
        assert pipeline.phase_ready(pid,'understand')[0]
        listed=c.get(f'/api/projects/{pid}/analysis/files',headers=h).json()
        assert listed['selected_files']==['book.cbl']
        assert c.put(f'/api/projects/{pid}/analysis/selection',headers=h,json={'files':['../secret.txt']}).status_code==400
        assert c.put(f'/api/projects/{pid}/analysis/selection',headers=h,json={'files':['book.cbl']}).status_code==200
        assert c.post(f'/api/projects/{pid}/analysis/consent',headers=h,json={'approved':False}).json()['approved'] is False
        assert not pipeline.phase_ready(pid,'understand')[0]
        reviews=c.get(f'/api/projects/{pid}/analysis/reviews',headers=h).json()
        assert len(reviews)>=1
        rid=reviews[0]['id']
        assert c.patch(f'/api/projects/{pid}/analysis/reviews/{rid}',headers=h,json={'status':'confirmed','comment':'Revisado'}).status_code==200
        assert c.get(f'/api/projects/{pid}/analysis/reviews',headers=h).json()[0]['status']=='confirmed'
        assert c.get(f'/api/projects/{pid}/analysis/reviews').status_code==401
        # Re-import the same filename: decisions and approvals must not leak to another snapshot.
        second=c.post(f'/api/projects/{pid}/upload',headers=h,files={'file':('again.zip',blob.getvalue())})
        for _ in range(200):
            job2=db.job_get(pid,second.json()['id'])
            if job2['status'] not in ('queued','running'):break
            time.sleep(.015)
        assert job2['status']=='completed',job2
        assert c.get(f'/api/projects/{pid}/analysis/consent',headers=h).json()['approved'] is False
        later=c.get(f'/api/projects/{pid}/analysis/reviews',headers=h).json()
        assert later and all(row['status']=='pending' for row in later)
        assert set(row['id'] for row in later).isdisjoint({rid})
