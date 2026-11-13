import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpInterceptorFn } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Provider { id: 'codex' | 'claude' | 'demo'; name: string; ready: boolean; help: string; }
export interface Run { id: string; phase: string; status: 'running' | 'completed' | 'failed';
  started_at: string; finished_at?: string; error?: string; summary?: string; provider: string;
  data: Record<string, any>;
}
export interface IngestJob { id:string; project_id:string;kind:string;status:string;stage:string;progress:number;
  error?:string;result?:{files:number;snapshot_id:string;snapshot_hash:string};created_at:string;retry_of?:string;
}
export interface Snapshot { id: string; origin_type: string; origin_reference: string;
  commit_sha: string | null; source_hash: string; file_count: number; total_bytes:number; created_at:string;
}
export interface Project { id: string; name: string; system_name: string; provider: string;
  created_at: string; source_filename?: string; snapshot_hash?: string; active_snapshot_id?: string | null;
  plan_approved: number | null; migration_decision: string | null;
  runs?: Run[]; artifacts?: string[]; stages?: string[]; phase_ready?: Record<string, boolean>;
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = sessionStorage.getItem('legacylift_session');
  return next(token && !req.url.endsWith('/auth/login') && !req.url.endsWith('/auth/register')
    ? req.clone({setHeaders: {Authorization: `Bearer ${token}`}}) : req);
};

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = '/api';
  login(email: string, password: string): Observable<{access_token: string}> {
    return this.http.post<{access_token: string}>(`${this.base}/auth/login`, {email, password});
  }
  register(email: string, password: string, display_name: string, bootstrap_secret: string): Observable<{access_token: string}> {
    return this.http.post<{access_token: string}>(`${this.base}/auth/register`, {email, password, display_name, bootstrap_secret});
  }
  authConfig(): Observable<{registration_open: boolean;bootstrap_required:boolean}> { return this.http.get<{registration_open: boolean;bootstrap_required:boolean}>(`${this.base}/auth/config`); }
  logout(): Observable<{ok: boolean}> { return this.http.post<{ok: boolean}>(`${this.base}/auth/logout`, {}); }
  me(): Observable<{username: string}> { return this.http.get<{username: string}>(`${this.base}/auth/me`); }
  providers(): Observable<Provider[]> { return this.http.get<Provider[]>(`${this.base}/providers`); }
  projects(): Observable<Project[]> { return this.http.get<Project[]>(`${this.base}/projects`); }
  create(name: string, system_name: string, provider: string): Observable<Project> {
    return this.http.post<Project>(`${this.base}/projects`, {name, system_name, provider});
  }
  rename(pid: string, name: string, system_name: string): Observable<Project> {
    return this.http.patch<Project>(`${this.base}/projects/${pid}`, {name,system_name});
  }
  githubStatus(): Observable<{configured: boolean; connection: {github_login: string} | null}> {
    return this.http.get<{configured:boolean;connection:{github_login:string}|null}>(`${this.base}/github/status`);
  }
  githubConnect(): Observable<{url:string}> { return this.http.post<{url:string}>(`${this.base}/github/connect`, {}); }
  githubDisconnect(): Observable<{ok:boolean}> { return this.http.post<{ok:boolean}>(`${this.base}/github/disconnect`, {}); }
  githubRepos(): Observable<{full_name:string;private:boolean;default_branch:string}[]> {
    return this.http.get<{full_name:string;private:boolean;default_branch:string}[]>(`${this.base}/github/repos`);
  }
  project(pid: string): Observable<Project> { return this.http.get<Project>(`${this.base}/projects/${pid}`); }
  jobs(pid: string): Observable<IngestJob[]> { return this.http.get<IngestJob[]>(`${this.base}/projects/${pid}/jobs`); }
  retry(pid: string, jid: string): Observable<IngestJob> { return this.http.post<IngestJob>(`${this.base}/projects/${pid}/jobs/${jid}/retry`,{}); }
  cancel(pid: string, jid: string): Observable<{ok:boolean}> { return this.http.post<{ok:boolean}>(`${this.base}/projects/${pid}/jobs/${jid}/cancel`,{}); }
  snapshots(pid: string): Observable<Snapshot[]> { return this.http.get<Snapshot[]>(`${this.base}/projects/${pid}/snapshots`); }
  activateSnapshot(pid: string, sid: string): Observable<Snapshot> {
    return this.http.post<Snapshot>(`${this.base}/projects/${pid}/snapshots/${sid}/activate`, {});
  }
  importGit(pid: string, full_name: string): Observable<IngestJob> {
    return this.http.post<IngestJob>(`${this.base}/projects/${pid}/git`,{full_name});
  }
  demoZip(): Observable<Blob> { return this.http.get('/demo-source.zip', {responseType: 'blob'}); }
  upload(pid: string, file: File): Observable<IngestJob> {
    const body = new FormData(); body.append('file', file);
    return this.http.post<IngestJob>(`${this.base}/projects/${pid}/upload`, body);
  }
  run(pid: string, phase: string): Observable<Run> { return this.http.post<Run>(`${this.base}/projects/${pid}/phases/${phase}`, {}); }
  plan(pid: string, approved: boolean): Observable<any> {
    return this.http.post(`${this.base}/projects/${pid}/plan/decision`, {approved});
  }
  decision(pid: string, approved: boolean): Observable<any> {
    return this.http.post(`${this.base}/projects/${pid}/migration/decision`, {approved});
  }
  artifact(pid: string, filename: string): Observable<string> {
    return this.http.get(`${this.base}/projects/${pid}/artifacts/${encodeURIComponent(filename)}`, { responseType: 'text' });
  }
  export(pid: string): Observable<Blob> {
    return this.http.get(`${this.base}/projects/${pid}/export`, {responseType: 'blob'});
  }
}
