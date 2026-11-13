/** Architectural contract. This runs without npm dependencies or an Angular build. */
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = join(root, 'src/app');
const read = f => readFileSync(f,'utf8');
const allFiles = dir => readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?allFiles(join(dir,e.name)):[join(dir,e.name)]);
const ts = allFiles(src).filter(f=>f.endsWith('.component.ts'));
const fail=[];
const check=(condition,label)=>{console.log(`${condition?'PASS':'FAIL'} ${label}`);if(!condition)fail.push(label)};
for(const file of ts){
  const dir=dirname(file); const name=file.split('/').at(-1).slice(0,-3);
  const source=read(file);
  check(existsSync(join(dir,name+'.html')) && existsSync(join(dir,name+'.css')), relative(src,file)+' has colocalized HTML and CSS');
  check(source.includes(`templateUrl: './${name}.html'`) && source.includes(`styleUrl: './${name}.css'`), relative(src,file)+' references own views');
  check(source.includes('standalone: true'), relative(src,file)+' is standalone');
}
const featureFiles=allFiles(join(src,'features'));
const globals=allFiles(join(root,'src/styles')).map(f=>relative(join(root,'src'),f));
check(!globals.some(f=>/layout|responsive|auth|sidebar|projects|pipeline|artifacts/.test(f)), 'No feature-specific global CSS');
check(!read(join(src,'app.component.ts')).includes('this.api.'),'Root does not perform API calls');
check(!read(join(src,'core/state/workspace.facade.ts')).includes('/features/'),'Core state does not depend on feature UI');
check(featureFiles.filter(f=>f.endsWith('.component.ts')).length >= 10,'Feature-first decomposition');
check(read(join(root,'package.json')).includes('"^22.2.0"'),'Angular 22 dependencies configured');
if(fail.length){console.error(`Architecture contract: ${fail.length} failures`);process.exitCode=1;}
else console.log(`Architecture contract: ${ts.length} components validated.`);
