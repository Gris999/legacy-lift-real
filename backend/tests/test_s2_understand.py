import json
import io
import time
import zipfile
from fastapi.testclient import TestClient
from app.api import app
from app import db,ai,pipeline


def test_understand_marks_ai_rules_as_unconfirmed_and_excludes_unselected_files(tmp_path, monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    with TestClient(app) as c:
        reg=c.post('/api/auth/register',json={'email':'analysis@test.test','display_name':'Analyst','password':'long-password-123456','bootstrap_secret':'bootstrap-test-secret-with-32-plus-characters'})
        h={'Authorization':'Bearer '+reg.json()['access_token']}
        pid=c.post('/api/projects',headers=h,json={'name':'Ventas','system_name':'Python','provider':'claude'}).json()['id']
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            z.writestr('orders.py','def total(x):\n    return x\n')
            z.writestr('internal.py','SECRET_INTERNAL_NOTE = 42\n')
        jid=c.post(f'/api/projects/{pid}/upload',headers=h,files={'file':('test.zip',b.getvalue())}).json()['id']
        for _ in range(200):
            if db.job_get(pid,jid)['status'] not in ('queued','running'):break
            time.sleep(.015)
        assert db.job_get(pid,jid)['status']=='completed'
        selection=c.put(f'/api/projects/{pid}/analysis/selection',headers=h,json={'files':['orders.py']})
        assert selection.status_code==200,selection.text
        c.post(f'/api/projects/{pid}/analysis/consent',headers=h,json={'approved':True})
        prompts=[]
        def fake_generate(provider,prompt,source,edit=False):
            prompts.append(prompt)
            return json.dumps({'summary':'Sistema con pedidos', 'business_rules':[
                 {'statement':'El pedido tiene total','evidence':[{'file':'orders.py','line':1}]},
                 {'statement':'Regla no verificada','evidence':[{'file':'fake.py','line':100}]}],
                'questions':['Verificar las reglas']})
        monkeypatch.setattr(ai,'generate',fake_generate)
        result,doc=pipeline.perform(pid,'understand')
        assert '2 reglas candidatas' in result
        assert len(prompts)==1
        assert 'orders.py' in prompts[0]
        assert 'SECRET_INTERNAL_NOTE' not in prompts[0]
        assert doc['business_rules'][0]['evidence_location_checked'] is True
        assert doc['business_rules'][0]['review_status']=='pending'
        assert doc['business_rules'][1]['evidence_location_checked'] is False
        assert doc['coverage']['files_omitted']==0
        assert len(c.get(f'/api/projects/{pid}/analysis/reviews',headers=h).json())==2
