import io
import zipfile
from test_flow import client,headers
from test_s4_review import prepared
from app import migration_verify,migration_runs,workspace


def ready(client):
    pid,aid=prepared(client)
    response=client.post(f'/api/projects/{pid}/phases/verify',headers=headers())
    assert response.status_code==200,response.text
    assert migration_verify.run_one()['verify_status']=='completed'
    return pid,aid


def test_accept_requires_explicit_risk_and_exports_reviewed_code(client):
    pid,aid=ready(client)
    url=f'/api/projects/{pid}/migration/decision'
    assert client.post(url,headers=headers(),json={'approved':True}).status_code==409
    assert client.get(f'/api/projects/{pid}/migration/delivery',headers=headers()).status_code==409
    response=client.post(url,headers=headers(),json={'approved':True,'reason':'Acepto el riesgo documentado: no hay comparación de pruebas automatizadas.'})
    assert response.status_code==200,response.text
    data=client.get(f'/api/projects/{pid}/migration/delivery',headers=headers())
    assert data.status_code==200
    with zipfile.ZipFile(io.BytesIO(data.content)) as z:
        assert 'codigo-modernizado/calculator.py' in z.namelist()
        assert 'evidencias/changes.patch' in z.namelist()
        assert 'evidencias/verify.json' in z.namelist()
        assert 'evidencias/manifest.json' in z.namelist()
    assert client.get(f'/api/projects/{pid}/migration/delivery?format=patch',headers=headers()).status_code==200
    assert client.post(url,headers=headers(),json={'approved':True,'reason':'Segundo intento'}).status_code==409


def test_reject_does_not_delete_immutable_candidate(client):
    pid,aid=ready(client)
    res=client.post(f'/api/projects/{pid}/migration/decision',headers=headers(),json={'approved':False,'reason':'No pasa nuestra revisión'})
    assert res.status_code==200,res.text
    assert migration_runs.candidate_path(pid,aid).exists()
    assert client.get(f'/api/projects/{pid}/migration/delivery',headers=headers()).status_code==409
    assert (workspace.project_source(pid)/'calculator.py').read_text().find('return (x + 1)')>0
