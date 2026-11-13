/** Regression tests for browser session persistence, without Angular runtime. */
import assert from 'node:assert/strict';
import {mkdtempSync, readFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
const root=join(dirname(fileURLToPath(import.meta.url)),'..');
const tmp=mkdtempSync(join(tmpdir(),'legacylift-auth-test-'));
const checks=[];
const test=(name,fn)=>{fn();checks.push(name);console.log('PASS '+name);};
const require=createRequire(import.meta.url);
class MemoryStorage {
  data=new Map();
  getItem(k){return this.data.get(k) ?? null;}
  setItem(k,v){this.data.set(k,v);}
  removeItem(k){this.data.delete(k);}
}
try {
  const compiler=join(root,'node_modules/.bin/tsc');
  const compileArgs=(bin)=> {
    const version=execFileSync(bin,['--version'],{encoding:'utf8'});
    // TypeScript 6 requires --ignoreConfig when compiling a standalone file.
    const major=Number(version.match(/(\d+)\./)?.[1]||0);
    return [ ...(major>=6?['--ignoreConfig']:[]), '--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--strict','--skipLibCheck','--outDir',tmp,join(root,'src/app/core/auth/session-store.ts') ];
  };
  try {execFileSync(compiler,compileArgs(compiler),{stdio:'inherit'});}
  catch (error) {
    // Also supports the global TypeScript compiler in lightweight dev environments.
    if(error?.code==='ENOENT') execFileSync('tsc',compileArgs('tsc'),{stdio:'inherit'});
    else throw error;
  }
  const lib=require(join(tmp,'session-store.js'));
  const token='sample-token-012345678901234567890123456789';
  const now=Date.parse('2026-11-13T12:00:00Z');
  const future=new Date(now+2_000_000).toISOString();
  test('Serialize and restore an unexpired token',()=>{
    const saved=lib.createStoredSession(token,future,{username:'Cuenta nueva'},now);
    assert.equal(lib.parseStoredSession(JSON.stringify(saved),now).user.username,'Cuenta nueva');
  });
  test('Reject expired and malformed sessions',()=>{
    assert.equal(lib.parseStoredSession(JSON.stringify({access_token:token,expires_at:new Date(now-10).toISOString()}),now),null);
    assert.equal(lib.parseStoredSession('{"access_token":"broken"}',now),null);
    assert.equal(lib.parseStoredSession('not-json',now),null);
  });
  test('Migrate Sprint 1 sessionStorage token to persistent store',()=>{
    const persistent=new MemoryStorage();const old=new MemoryStorage();old.setItem(lib.LEGACY_AUTH_STORAGE_KEY,token);
    assert.equal(lib.restoreStoredSession(persistent,old,now).access_token,token);
    assert.equal(old.getItem(lib.LEGACY_AUTH_STORAGE_KEY),null);
    assert.ok(persistent.getItem(lib.AUTH_STORAGE_KEY));
  });
  test('Persistent session survives reload and preserves user name',()=>{
    const persistent=new MemoryStorage();
    persistent.setItem(lib.AUTH_STORAGE_KEY,JSON.stringify(lib.createStoredSession(token,future,{username:'Andrés'},now)));
    assert.equal(lib.restoreStoredSession(persistent,new MemoryStorage(),now+60_000).user.username,'Andrés');
  });
  test('Expired persistent session cannot be restored',()=>{
    const persistent=new MemoryStorage();
    persistent.setItem(lib.AUTH_STORAGE_KEY,JSON.stringify(lib.createStoredSession(token,future,null,now)));
    assert.equal(lib.restoreStoredSession(persistent,new MemoryStorage(),now+3_000_000),null);
    assert.equal(persistent.getItem(lib.AUTH_STORAGE_KEY),null);
  });
  test('Malformed legacy token cannot be migrated',()=>{
    const old=new MemoryStorage();old.setItem(lib.LEGACY_AUTH_STORAGE_KEY,'short');
    assert.equal(lib.restoreStoredSession(new MemoryStorage(),old,now),null);
  });
  test('Backend expiration is honored, not extended on reload',()=>{
    assert.equal(lib.createStoredSession(token,future,null,now).expires_at,future);
  });
  const facade=readFileSync(join(root,'src/app/core/state/workspace.facade.ts'),'utf8');
  const api=readFileSync(join(root,'src/app/core/api/api.service.ts'),'utf8');
  test('A temporary auth/me error never revokes the session',()=>{
    assert.ok(facade.includes('this.sessionCheckFailed=true'));
    assert.ok(!facade.includes('error: () => this.logout()'));
    assert.ok(facade.includes('this.session.rememberUser(user, token)'));
  });
  test('Global auth interceptor clears only HTTP 401',()=>{
    assert.ok(api.includes('error.status === 401'));
    assert.ok(api.includes('session.clear(token)'));
    assert.ok(!api.includes("sessionStorage.getItem('legacylift_session')"));
  });
  test('SSE reads token from the same session service',()=>{
    assert.ok(facade.includes('const token=this.session.token'));
    assert.ok(!facade.includes("sessionStorage.getItem('legacylift_session')"));
  });
  console.log(`${checks.length}/${checks.length} checks passed`);
} finally {rmSync(tmp,{recursive:true,force:true});}
