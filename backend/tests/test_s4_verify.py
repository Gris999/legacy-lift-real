from test_flow import client,headers
from test_s4_review import prepared
from app import db,pipeline,migration_verify,migration_runs,migration_review


def test_verify_default_avoids_fake_equivalence(client):
    pid,aid=prepared(client)
    response=client.post(f'/api/projects/{pid}/phases/verify',headers=headers())
    assert response.status_code==200,response.text
    assert response.json()['status']=='queued'
    result=migration_verify.run_one()
    assert result['verify_status']=='completed',result
    report=result['verification']
    assert report['classification']=='not_demonstrated',report
    assert report['confidence_score'] is None
    assert report['reviewed_sha256']
    assert db.last_run(pid,'verify')['status']=='completed'


def test_review_invalidates_verify_and_needs_new_execution(client):
    pid,aid=prepared(client)
    assert migration_verify.enqueue(pid)
    assert migration_verify.run_one()['verification']
    row=migration_review.summary(pid,aid)['files'][0]
    changed=migration_review.review(pid,aid,db.project_get(pid)['owner_id'],row['path'],False,'No conservar')
    assert changed['selected_count']==0
    assert migration_runs.get(pid,aid)['verification'] is None
    assert db.last_run(pid,'verify')['status']=='superseded'
    assert client.post(f'/api/projects/{pid}/phases/verify',headers=headers()).status_code==409


def test_comparison_rejects_zero_and_failed_tests():
    st={'static_checks':{'failed':0}}
    old={**st,'tests':{'status':'passed','output':'Ran 0 tests in 0.0s'}}
    new={**st,'tests':{'status':'passed','output':'Ran 0 tests in 0.0s'}}
    assert migration_verify.comparison(old,new)['classification']=='divergent'
    new['tests']={'status':'failed','output':'assert error'}
    assert migration_verify.comparison(old,new)['classification']=='divergent'
