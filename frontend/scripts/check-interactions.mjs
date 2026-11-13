/** Regression contract for Angular 22 OnPush / signal-driven cross-component UI.
 * This check runs without browsers; npm run build covers Angular template compilation.
 */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=join(dirname(fileURLToPath(import.meta.url)), '..');
const read=p=>readFileSync(join(root,p),'utf8');
const facade=read('src/app/core/state/workspace.facade.ts');
const app=read('src/app/app.component.html');
const dialogs=read('src/app/features/projects/project-dialogs/project-dialogs.component.html');
const sidebar=read('src/app/features/shell/project-sidebar/project-sidebar.component.html');
const dashboard=read('src/app/features/projects/project-dashboard/project-dashboard.component.html');
const login=read('src/app/features/auth/auth-page/auth-page.component.html');
const review=read('src/app/features/analysis/review-queue/review-queue.component.html');
const session=read('src/app/core/auth/auth-session.service.ts');
const checks=[];
const check=(name,fn)=>{fn();checks.push(name);console.log('PASS '+name);};
const isReactive=field=>{
  assert.match(facade, new RegExp(`private readonly _${field}\\s*=\\s*signal<`));
  assert.match(facade, new RegExp(`get ${field}\\(\\):[^\\n]+this\\._${field}\\(\\)`));
  assert.match(facade, new RegExp(`set ${field}\\(value:[^\\n]+this\\._${field}\\.set\\(value\\)`));
};
check('login and logout change a signal read by AppComponent',()=>{
  isReactive('authenticated');assert.match(app,/\*ngIf="!vm.authenticated"/);assert.match(app,/\*ngIf="vm.authenticated"/);
  assert.match(facade,/this\.session\.save\(/);assert.match(facade,/this\.authenticated\s*=\s*!!nextToken/);
});
check('login loading indicator is reactive to HTTP completion',()=>{
  isReactive('busy');assert.match(login,/vm\.busy\?'/);assert.match(facade,/this\.busy=false/);
});
check('both project actions update the same reactive dialog flag',()=>{
  isReactive('showCreate');assert.match(sidebar,/vm\.showCreate=true/);assert.match(dashboard,/vm\.showCreate=true/);
  assert.match(dialogs,/\[open\]="vm\.showCreate && vm\.authenticated"/);
});
check('project creation updates reactive project list and selection',()=>{
  isReactive('projects');isReactive('selected');isReactive('createName');isReactive('createSystem');
  assert.match(dialogs,/\(ngSubmit\)="vm\.create\(\)"/);assert.match(facade,/this\.api\.create\(/);
});
check('user identity and error handling update on asynchronously restored sessions',()=>{
  isReactive('currentUser');isReactive('error');isReactive('registrationOpen');
  assert.match(facade,/this\.session\.rememberUser\(/);assert.match(session,/localStorage\.setItem/);
});
check('cross-component sidebar, modal and onboarding state is reactive',()=>{
  for(const field of ['mobileNavOpen','showHelp','showEdit','passwordVisible','providers','snapshots','ingestJobs'])isReactive(field);
});
check('analysis state and review drafts notify OnPush components',()=>{
  for(const field of ['scanProgress','discoverData','assessmentData','reviews','reviewDraft','selectedFilePaths'])isReactive(field);
  assert.match(review,/vm\.setReviewDraft\(item.id, \$event\)/);
  assert.doesNotMatch(facade,/this\.selected\.code_consent\s*=/);
});
console.log(`${checks.length}/${checks.length} interactions checks passed`);
