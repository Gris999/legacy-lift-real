from test_flow import client,headers
from test_s3_baseline import ready_project
from app import db,pipeline,migration_runs,migration_review,workspace


def prepared(client):
    pid=ready_project(client)
    summary,data=pipeline.perform(pid,'baseline')
    rid=db.run_create(pid,'baseline','demo');db.run_complete(rid,summary,data)
    result=client.post(f'/api/projects/{pid}/phases/modernize',headers=headers())
    assert result.status_code==200,result.text
    aid=result.json()['id']
    assert migration_runs.run_one()['status']=='completed'
    return pid,aid


def test_review_summary_full_diff_and_whole_file_selection(client):
    pid,aid=prepared(client)
    details=client.get(f'/api/projects/{pid}/migration/attempts/{aid}/review',headers=headers())
    assert details.status_code==200
    item=details.json()['files'][0];assert item['selected'] and item['added'] and item['removed']
    assert 'return x + 1' in client.get(f'/api/projects/{pid}/migration/attempts/{aid}/diff',params={'path':item['path']},headers=headers()).json()['diff']
    assert client.get(f'/api/projects/{pid}/migration/attempts/{aid}/diff',params={'path':'../.env'},headers=headers()).status_code==409
    r=client.patch(f'/api/projects/{pid}/migration/attempts/{aid}/review',headers=headers(),json={'path':item['path'],'selected':False,'comment':'Conservar implementación'})
    assert r.status_code==200 and r.json()['selected_count']==0
    assert (workspace.project_source(pid)/item['path']).read_text().find('return (x + 1)')>0
    assert client.patch(f'/api/projects/{pid}/migration/attempts/{aid}/review',headers=headers(),json={'path':item['path'],'selected':True,'comment':'Aceptar cambio'}).status_code==200
    reviewed,digest=migration_review.assemble(pid,aid)
    assert (reviewed/item['path']).read_text().find('return x + 1')>0
    assert digest==workspace.snapshot_hash(reviewed)
