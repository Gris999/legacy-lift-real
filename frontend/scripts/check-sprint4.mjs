/** No-dependency static contract guard for the Modernize Safely feature. */
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=join(dirname(fileURLToPath(import.meta.url)),'..','src','app');
const rd=x=>readFileSync(join(root,x),'utf8');
const checks=[];
function check(ok,label){checks.push([ok,label]);console.log(`${ok?'PASS':'FAIL'} ${label}`)}
const dash=rd('features/projects/project-dashboard/project-dashboard.component.html');
const dashTs=rd('features/projects/project-dashboard/project-dashboard.component.ts');
const api=rd('core/api/api.service.ts');
const state=rd('core/state/workspace.facade.ts');
for (const name of ['migration-review','verify-result']){
 const path=`features/migration/${name}/${name}.component`;
 check(['ts','html','css'].every(ext=>existsSync(join(root,path+'.'+ext))),`${name}: TS, HTML and CSS separate`);
 check(rd(path+'.ts').includes('templateUrl:') && rd(path+'.ts').includes('styleUrl:'),`${name}: external view and styles`);
}
check(dash.includes('<ll-migration-review') && dash.includes('<ll-verify-result'),'Migration and verification views connected');
check(dashTs.includes('MigrationReviewComponent') && dashTs.includes('VerifyResultComponent'),'Standalone components declared');
check(api.includes('/migration/attempts') && api.includes('/migration/delivery'),'Attempt and delivery APIs connected');
check(api.includes('/migration/attempts/${aid}/review') && api.includes('/migration/attempts/${aid}/diff'),'Review and full diff endpoints connected');
check(state.includes('signal<MigrationAttempt[]>') && state.includes('signal<MigrationReviewSummary|null>'),'Migration reactive state uses signals');
check(state.includes('loadMigration(pid)') && state.includes("evt.kind==='migration'"),'SSE and refresh route to migration state');
check(!rd('features/pipeline/phase-actions/phase-actions.component.html').includes('(click)="vm.migrationDecision(true)"'),'Approval not possible without Verify risk review');
check(rd('features/migration/migration-review/migration-review.component.html').includes('diff completo'),'Full technical diff is opt-in');
check(rd('features/migration/verify-result/verify-result.component.html').includes('Motivo') && rd('features/migration/verify-result/verify-result.component.html').includes('migrationRiskReason'),'Human reason for insufficient verification');
check(!rd('features/migration/migration-review/migration-review.component.css').includes('#8fe3d8'),'No legacy accent colors');
if(checks.some(x=>!x[0]))process.exitCode=1;
else console.log(`Sprint 4 frontend contract: ${checks.length}/${checks.length} passed.`);
