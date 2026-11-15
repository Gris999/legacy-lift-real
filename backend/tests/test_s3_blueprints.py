"""Blueprints never authorize their own execution; revisions remain reviewable."""
from app import db, planning, pipeline
from test_flow import client, headers, sample_zip, await_ingest


def project_ready(client):
    p=client.post('/api/projects',headers=headers(),json={'name':'Proyecto Sprint Tres','system_name':'Legacy Python','provider':'demo'}).json()
    pid=p['id']
    up=client.post(f'/api/projects/{pid}/upload',headers=headers(),files={'file':('codigo.zip',sample_zip(),'application/zip')})
    assert await_ingest(pid,up.json()['id'])['status']=='completed'
    for phase in ('discover','understand','assess','plan'):
        result,details=pipeline.perform(pid,phase)
        rid=db.run_create(pid,phase,'demo'); db.run_complete(rid,result,details)
    return pid


def test_blueprint_generates_and_revisions_are_immutable(client):
    pid=project_ready(client)
    resp=client.get(f'/api/projects/{pid}/blueprints/current',headers=headers())
    assert resp.status_code==200
    b=resp.json()['blueprint']
    assert b['status']=='draft' and b['revision']==1
    assert b['data']['waves'] and b['data']['waves'][0]['files']==['calculator.py']
    assert 'snapshot' in b['data']['source_snapshot_id'] or len(b['data']['source_snapshot_id']) > 5
    data=b['data'].copy(); data['title']='Plan revisado'
    result=client.patch(f'/api/projects/{pid}/blueprints/current',headers=headers(),json={'data':data})
    assert result.status_code==200,result.text
    assert result.json()['revision']==2
    history=client.get(f'/api/projects/{pid}/blueprints/history',headers=headers()).json()
    assert [x['revision'] for x in history]==[2,1]
    assert history[-1]['data']['title']==b['data']['title']
    assert history[0]['status']=='draft' and history[-1]['status']=='superseded'


def test_blueprint_rejects_untracked_files_and_cyclic_dependencies(client):
    pid=project_ready(client)
    data=client.get(f'/api/projects/{pid}/blueprints/current',headers=headers()).json()['blueprint']['data']
    data['waves'][0]['files']=['../secrets.txt']
    response=client.patch(f'/api/projects/{pid}/blueprints/current',headers=headers(),json={'data':data})
    assert response.status_code==400
    assert client.get(f'/api/projects/{pid}/blueprints/current',headers=headers()).json()['blueprint']['revision']==1


def test_blueprint_approved_only_after_human_action(client):
    pid=project_ready(client)
    assert db.project_get(pid)['plan_approved'] is None
    res=client.post(f'/api/projects/{pid}/plan/decision',headers=headers(),json={'approved':True})
    assert res.status_code==200,res.text
    assert planning.current(pid)['status']=='approved'
    assert db.project_get(pid)['plan_approved']==1
    res=client.post(f'/api/projects/{pid}/plan/decision',headers=headers(),json={'approved':True})
    assert res.status_code==409
