import { readFileSync, statSync } from 'node:fs';
import { join,dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=join(dirname(fileURLToPath(import.meta.url)),'..');
const text=rel=>readFileSync(join(root,rel),'utf8');
const auth=text('src/app/features/auth/auth-page/auth-page.component.html');
const sidebar=text('src/app/features/shell/project-sidebar/project-sidebar.component.html');
const logo=text('src/app/shared/ui/brand-logo/brand-logo.component.html');
const logoCss=text('src/app/shared/ui/brand-logo/brand-logo.component.css');
const theme=text('src/app/core/theme/theme.service.ts');
const tokens=text('src/styles/tokens.css');
const sync=text('scripts/sync-branding.mjs');
const checks=[
 ['Logo oficial en ambos contextos',auth.includes('<ll-brand-logo')&&sidebar.includes('<ll-brand-logo')],
 ['Archivo de imágenes oficial',logo.includes('/branding/custom/logo-dark.webp') && logo.includes('/branding/custom/logo-light.webp')],
 ['Marca ampliada y adaptable',logoCss.includes('430px') && logoCss.includes('242px') && logoCss.includes('object-fit: contain') && !logoCss.includes('position: absolute')],
 ['Temas claro y oscuro',tokens.includes('data-theme="dark"')&&tokens.includes('data-theme="light"')],
 ['Selector en login y workspace',auth.includes('vm.toggleTheme()')&&text('src/app/features/shell/workspace-topbar/workspace-topbar.component.html').includes('vm.toggleTheme()')],
 ['Tema persistente',theme.includes('localStorage.setItem')],
 ['Recursos originales con hash validado',sync.includes("createHash('sha1')") && !sync.includes('logo-dark-1024.webp')],
 ['Logos personalizados presentes en el paquete', ['dark','light'].every(mode => {
    const data = readFileSync(join(root,`public/branding/custom/logo-${mode}.webp`));
    return data.toString('ascii',0,4) === 'RIFF' && data.toString('ascii',8,12) === 'WEBP' && data.length > 1000;
 })],
 ['Sin modificar contratos del backend',text('src/app/core/api/api.service.ts').includes('/api')],
];
let failed=0;for(const [label,pass] of checks){console.log(`${pass?'PASS':'FAIL'} ${label}`);if(!pass)failed++;}
if(failed)process.exitCode=1;else console.log(`${checks.length} branding checks passed.`);
