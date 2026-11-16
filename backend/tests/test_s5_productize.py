"""Sprint 5 regression tests: tenant isolation, invitations, RBAC and reports."""
import pytest
from fastapi.testclient import TestClient
from app.api import app

@pytest.fixture
def env(tmp_path,monkeypatch):
    monkeypatch.setenv('LEGACYLIFT_DATA_DIR',str(tmp_path/'data'))
    monkeypatch.setenv('LEGACYLIFT_ALLOW_REGISTRATION','true')
    monkeypatch.setenv('LEGACYLIFT_BOOTSTRAP_SECRET','bootstrap-test-secret-with-32-plus-characters')
    with TestClient(app) as client:
        def account(email):
            payload={'email':email,'display_name':'User '+email.split('@')[0],
                     'password':'secure-pass-123456789','bootstrap_secret':'bootstrap-test-secret-with-32-plus-characters'}
            response=client.post('/api/auth/register',json=payload)
            assert response.status_code==200,response.text
            return {'Authorization':'Bearer '+response.json()['access_token']}
        yield client,account

def test_personal_org_keeps_existing_project_flow(env):
    client,account=env
    user=account('first@test.local')
    response=client.post('/api/projects',headers=user,json={'name':'Proyecto A','system_name':'PHP','provider':'demo'})
    assert response.status_code==200,response.text
    p=response.json()
    assert client.get('/api/projects',headers=user).json()[0]['id']==p['id']
    orgs=client.get('/api/organizations',headers=user).json()
    assert orgs[0]['id']==p['organization_id'] and orgs[0]['role']=='owner'

def test_isolation_membership_invites_and_roles(env):
    client,account=env
    owner=account('owner@test.local')
    stranger=account('stranger@test.local')
    org=client.post('/api/organizations',headers=owner,json={'name':'Equipo Alfa'}).json()['id']
    p=client.post('/api/projects',headers=owner,
                  json={'name':'Proyecto seguro','system_name':'COBOL','provider':'demo','organization_id':org}).json()['id']
    assert client.get('/api/projects/'+p,headers=stranger).status_code==404
    assert client.get('/api/organizations/'+org+'/reports',headers=stranger).status_code==404
    assert all(x['id']!=p for x in client.get('/api/projects',headers=stranger).json())
    invitation=client.post('/api/organizations/'+org+'/invitations',headers=owner,
                  json={'email':'stranger@test.local','role':'viewer'})
    assert invitation.status_code==200,invitation.text
    token=invitation.json()['token']
    assert client.post('/api/organizations/invitations/accept',headers=owner,json={'token':token}).status_code==400
    assert client.post('/api/organizations/invitations/accept',headers=stranger,json={'token':token}).status_code==200
    assert client.post('/api/organizations/invitations/accept',headers=stranger,json={'token':token}).status_code==400
    assert client.get('/api/projects/'+p,headers=stranger).status_code==200
    assert client.patch('/api/projects/'+p,headers=stranger,
          json={'name':'No permitido','system_name':'PHP'}).status_code==403
    assert client.get('/api/organizations/'+org+'/members',headers=stranger).status_code==403
    members=client.get('/api/organizations/'+org+'/members',headers=owner).json()
    member=next(x['id'] for x in members if x['email']=='stranger@test.local')
    assert client.patch('/api/organizations/'+org+'/members/'+member,headers=owner,
                        json={'role':'developer'}).status_code==200
    assert client.patch('/api/projects/'+p,headers=stranger,
                        json={'name':'Renombrado','system_name':'PHP'}).status_code==200
    assert client.post('/api/organizations/'+org+'/invitations',headers=stranger,
                       json={'email':'new@test.local','role':'admin'}).status_code==403
    assert client.delete('/api/organizations/'+org+'/members/'+member,headers=owner).status_code==200
    assert client.get('/api/projects/'+p,headers=stranger).status_code==404

def test_reports_csv_audit_and_plan_usage(env):
    client,account=env
    owner=account('owner@test.local')
    org=client.post('/api/organizations',headers=owner,json={'name':'Informes'}).json()['id']
    p=client.post('/api/projects',headers=owner,
          json={'name':'=FORMULA','system_name':'PHP','provider':'demo','organization_id':org})
    assert p.status_code==200,p.text
    report=client.get('/api/organizations/'+org+'/reports',headers=owner).json()
    assert report['totals']['projects']==1
    assert report['projects'][0]['name']=='=FORMULA'
    csv=client.get('/api/organizations/'+org+'/reports.csv',headers=owner)
    assert csv.status_code==200 and "'=FORMULA" in csv.text
    usage=client.get('/api/organizations/'+org+'/usage',headers=owner).json()
    assert usage['billing']['payments_enabled'] is False
    audit=client.get('/api/organizations/'+org+'/audit',headers=owner).json()
    assert any(item['action']=='project.created' for item in audit)
    assert all('secure-pass' not in str(item) for item in audit)

def test_project_quota_and_owner_protection(env):
    client,account=env
    owner=account('owner@test.local')
    org=client.post('/api/organizations',headers=owner,json={'name':'Cuotas'}).json()['id']
    user=client.get('/api/organizations/'+org+'/members',headers=owner).json()[0]['id']
    assert client.delete('/api/organizations/'+org+'/members/'+user,headers=owner).status_code==403
    assert client.patch('/api/organizations/'+org+'/members/'+user,headers=owner,json={'role':'viewer'}).status_code==403
    for n in range(10):
        r=client.post('/api/projects',headers=owner,json={
            'name':f'Proyecto {n}', 'system_name':'Python','provider':'demo','organization_id':org})
        assert r.status_code==200,r.text
    assert client.post('/api/projects',headers=owner,json={
        'name':'Exceso', 'system_name':'Python','provider':'demo','organization_id':org}).status_code==409
