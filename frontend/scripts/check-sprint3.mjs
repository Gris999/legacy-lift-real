/** Sprint 3 cross-feature contract check; no npm modules required. */
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=join(dirname(fileURLToPath(import.meta.url)),'..');
const src=join(root,'src/app');
const rd=p=>readFileSync(join(src,p),'utf8');
const checks=[];
function check(ok,label){checks.push([ok,label]);console.log(`${ok?'PASS':'FAIL'} ${label}`)}
const dash=rd('features/projects/project-dashboard/project-dashboard.component.html');
const dashTs=rd('features/projects/project-dashboard/project-dashboard.component.ts');
const dashCss=rd('features/projects/project-dashboard/project-dashboard.component.css');
const api=rd('core/api/api.service.ts');
const vm=rd('core/state/workspace.facade.ts');
check(dash.includes('role="tablist"') && dash.includes('role="tab"') && dash.includes('role="tabpanel"'),'Workspace tabs expose semantic roles');
check(['source','discover','understand','assess','plan','baseline','modernize','verify','evidence'].every(t=>dashTs.includes(`id:'${t}'`)),'All nine stages available');
check(/position:\s*sticky/.test(dashCss) && /overflow-x:\s*auto/.test(dashCss),'Phase navigation sticky and horizontally scrollable');
for(const [dir,component] of [['blueprint-editor','ll-blueprint-editor'],['migration-packs','ll-migration-packs'],['baseline-panel','ll-baseline-panel']]){
 const base=`features/planning/${dir}/${dir}.component`;
 check(['ts','html','css'].every(ext=>existsSync(join(src,`${base}.${ext}`))),`${component} has dedicated TS, HTML and CSS`);
 check(new RegExp(`selector\\s*:\\s*['\"]${component}['\"]`).test(rd(`${base}.ts`)),`${component} selector is stable`);
}
check(dash.includes('<ll-blueprint-editor') && dash.includes('<ll-migration-packs') && dash.includes('<ll-baseline-panel'),'Planning views integrated into workspace');
check(api.includes('/blueprints/current') && api.includes('/migration-packs'),'Blueprint and pack APIs connected');
check(api.includes('/baseline/preflight') && api.includes('/baseline/consent') && api.includes('/baseline/suggestions'),'Baseline API and human consent connected');
check(vm.includes('loadBaselinePreflight') && vm.includes('authorizeExecution') && vm.includes('decideTestProposal'),'Facade exposes baseline controls');
check(rd('features/planning/baseline-panel/baseline-panel.component.html').includes('Autorizo la ejecución') && rd('features/planning/baseline-panel/baseline-panel.component.html').includes('Aprobar propuesta'),'Explicit worker consent and test-case approval UI');
check(dashCss.includes('var(--color-') && !dashCss.includes('#8fe3d8'),'Theme tokens preserved; no old brand accent');
if(checks.some(x=>!x[0]))process.exitCode=1;else console.log(`Sprint 3 contract: ${checks.length}/${checks.length} passed.`);
