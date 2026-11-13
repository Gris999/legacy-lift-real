/** Dependency-free regression checks for the Sprint 2 UI contracts. */
import {readFileSync,existsSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=join(dirname(fileURLToPath(import.meta.url)),'..');
const app=join(root,'src/app');
const read=(p)=>readFileSync(join(app,p),'utf8');
const checks=[
 ['Live language visual',read('features/analysis/discover-overview/discover-overview.component.html').includes('language-bar')],
 ['Code-based percentage caveat',read('features/analysis/discover-overview/discover-overview.component.html').includes('GitHub Linguist')],
 ['Interactive dependency graph',read('features/analysis/architecture-graph/architecture-graph.component.html').includes('(keydown.enter)')],
 ['Opt-in privacy controls',read('features/analysis/analysis-controls/analysis-controls.component.html').includes('updateCodeConsent')],
 ['File selection controls',read('features/analysis/analysis-controls/analysis-controls.component.html').includes('saveSourceSelection')],
 ['Review decisions',read('features/analysis/review-queue/review-queue.component.html').includes('updateReview')],
 ['Assessment visualization',read('features/analysis/assessment-overview/assessment-overview.component.html').includes('assessment-metrics')],
 ['No arbitrary score',read('features/analysis/assessment-overview/assessment-overview.component.html').includes('score_reason')],
 ['Facade loads selected snapshot analysis',read('core/state/workspace.facade.ts').includes('loadAssessment')],
 ['API includes review and consent',read('core/api/api.service.ts').includes('setAnalysisConsent')&&read('core/api/api.service.ts').includes('reviewItem')],
 ['Components have private CSS', ['discover-overview','architecture-graph','analysis-controls','review-queue','assessment-overview'].every(n=>{
   const file=join(app,'features/analysis',n,n+'.component.css');return existsSync(file);
 })]
];
let broken=0;for(const [name,ok] of checks){console.log(`${ok?'PASS':'FAIL'} ${name}`);if(!ok)broken++;}
if(broken){console.error(`${broken} Sprint 2 contracts broken`);process.exitCode=1;}
else console.log(`${checks.length} Sprint 2 UI contracts passed.`);
