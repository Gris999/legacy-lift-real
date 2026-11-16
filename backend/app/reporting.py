"""Tenant-scoped historical activity and CSV export (no source code or secrets)."""
from __future__ import annotations
import csv
import io
from datetime import datetime, timezone
from . import db, tenancy

def summary(oid:str,uid:str) -> dict:
    org=tenancy.organization(oid,uid)
    with db.connect() as c:
        projects=c.execute('SELECT COUNT(*) AS n FROM organization_projects WHERE organization_id=?',(oid,)).fetchone()['n']
        members=c.execute('SELECT COUNT(*) AS n FROM organization_members WHERE organization_id=?',(oid,)).fetchone()['n']
        by_phase=[dict(r) for r in c.execute("""SELECT r.phase,r.status,COUNT(*) AS count
            FROM phase_runs r JOIN organization_projects op ON op.project_id=r.project_id
            WHERE op.organization_id=? GROUP BY r.phase,r.status ORDER BY r.phase,r.status""",(oid,))]
        migrations=[dict(r) for r in c.execute("""SELECT a.status,COALESCE(a.decision,'pending') AS decision,COUNT(*) AS count
            FROM migration_attempts a JOIN organization_projects op ON op.project_id=a.project_id
            WHERE op.organization_id=? GROUP BY a.status,a.decision""",(oid,))]
        snapshots=c.execute("""SELECT COUNT(*) AS n FROM source_snapshots s
            JOIN organization_projects op ON op.project_id=s.project_id
            WHERE op.organization_id=?""",(oid,)).fetchone()['n']
        rows=[dict(r) for r in c.execute("""SELECT p.id,p.name,p.provider,p.created_at,p.migration_decision,
            (SELECT COUNT(*) FROM phase_runs WHERE project_id=p.id) AS runs,
            (SELECT COUNT(*) FROM migration_attempts WHERE project_id=p.id) AS attempts
            FROM projects p JOIN organization_projects op ON op.project_id=p.id
            WHERE op.organization_id=? ORDER BY p.created_at DESC LIMIT 100""",(oid,))]
    return {'organization':{'id':oid,'name':org['name'],'plan':org['plan_id']},
            'totals':{'projects':projects,'members':members,'snapshots':snapshots,
              'runs':sum(x['count'] for x in by_phase),'migration_attempts':sum(x['count'] for x in migrations)},
            'runs_by_phase':by_phase,'migration_decisions':migrations,'projects':rows}

def usage(oid:str,uid:str) -> dict:
    org=tenancy.organization(oid,uid)
    s=summary(oid,uid)
    period=datetime.now(timezone.utc).strftime('%Y-%m')
    with db.connect() as c:
        count=c.execute("""SELECT COUNT(*) AS n FROM phase_runs r JOIN organization_projects op
           ON op.project_id=r.project_id WHERE op.organization_id=? AND substr(r.started_at,1,7)=?""",
           (oid,period)).fetchone()['n']
    return {'plan':tenancy.PLANS[org['plan_id']],'period':period,
            'used':{'projects':s['totals']['projects'],'members':s['totals']['members'],'monthly_runs':count},
            'billing':{'status':'not_configured','payments_enabled':False,
                'message':'Planes y cuotas locales; no se realizan cobros ni se procesan tarjetas.'}}

def export_csv(oid:str,uid:str) -> str:
    report=summary(oid,uid)
    out=io.StringIO(); writer=csv.writer(out)
    writer.writerow(['Proyecto','Proveedor','Creado','Ejecuciones','Intentos','Decisión'])
    for p in report['projects']:
        fields=[p['name'],p['provider'],p['created_at'],p['runs'],p['attempts'],p['migration_decision'] or 'pending']
        # Escape spreadsheet-formula prefixes; names may originate from untrusted input.
        writer.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in fields])
    return out.getvalue()
