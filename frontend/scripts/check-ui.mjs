/** Lightweight UI regression contracts across the feature-first Angular views. */
import { readFileSync,readdirSync } from 'node:fs';
import { join,dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=join(dirname(fileURLToPath(import.meta.url)),'..');
const text=f=>readFileSync(join(root,f),'utf8');
const readAll=dir=>readdirSync(join(root,dir),{withFileTypes:true}).flatMap(e=>e.isDirectory()?readAll(dir+'/'+e.name):[text(dir+'/'+e.name)]).join('\n');
const view=readAll('src/app/features');
const rootView=text('src/app/app.component.html');
const theme=text('src/app/core/theme/theme.service.ts');
const base=text('src/styles/base.css');
const brand=text('src/app/shared/ui/brand-logo/brand-logo.component.html');
const checks=[
  ['Login and registration',view.includes('(ngSubmit)="vm.login()"')&&view.includes('vm.registerMode=!vm.registerMode')],
  ['Bootstrap setup protected',view.includes('vm.bootstrapRequired')&&view.includes('vm.bootstrapSecret')],
  ['Project selection',view.includes('vm.select(p.id)')],
  ['GitHub OAuth',view.includes('vm.connectGithub()')&&view.includes('vm.importRepository()')],
  ['ZIP, demo and jobs',view.includes('vm.upload($event)')&&view.includes('vm.loadDemo()')&&view.includes('vm.retryJob(j.id)')],
  ['Snapshots',view.includes('vm.activateSnapshot(snap.id)')],
  ['Pipeline and decisions',view.includes('vm.run()')&&view.includes('vm.planDecision(true)')&&view.includes('vm.migrationDecision(false)')],
  ['Evidence and export',view.includes('vm.openArtifact(f)')&&view.includes('vm.download()')],
  ['Theme toggle visible',view.includes('vm.toggleTheme()')&&theme.includes('localStorage.setItem')],
  ['Mobile sidebar functional',view.includes('vm.mobileNavOpen=true')&&view.includes('sidebar-open')],
  ['Shared UI icons and logo',view.includes('ll-brand-logo')&&brand.includes('logo-dark.webp')],
  ['Focus and reduced motion',base.includes(':focus-visible')&&text('src/styles/primitives.css').includes('prefers-reduced-motion')],
  ['Feature composition',rootView.includes('<ll-auth-page')&&rootView.includes('<ll-workspace-shell')],
];
let failed=0;for(const [label,pass] of checks){console.log(`${pass?'PASS':'FAIL'} ${label}`);if(!pass)failed++;}
if(failed)process.exitCode=1;else console.log(`${checks.length} UI checks passed.`);
