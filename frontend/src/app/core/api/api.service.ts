import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { AuthSessionService } from '../auth/auth-session.service';

export interface AuthResponse { access_token: string; token_type: string; expires_at: string; user?: { display_name: string; email: string; id: string }; }
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
  active_wave_id?:string|null; active_pack_id?:string|null;
  plan_approved: number | null; migration_decision: string | null; code_consent?: boolean;
  runs?: Run[]; artifacts?: string[]; stages?: string[]; phase_ready?: Record<string, boolean>;
}

export interface MigrationWave {id:string; goal:string; strategy:string; files:string[]; depends_on:string[];
  priority:number;risk:string;acceptance_criteria:string;}
export interface BlueprintData {schema_version:number;title:string;target_architecture:string;source_snapshot_id:string;
  waves:MigrationWave[]; notes:string;limitations:string;}
export interface BaselineTest {path:string;framework:string;}
export interface TestProposal {id:string;status:'pending'|'approved'|'rejected';data:{title:string;input:string;expected:string;evidence_file:string;source:string;note:string};}
export interface BaselinePreflight {ready:boolean;execution_authorized:boolean;worker_mode:string;tests:BaselineTest[];proposals:TestProposal[];}
export interface MigrationPack {id:string; name:string;status:'available'|'planned';version:string;
  strategies:string[];languages:string[];validators:string[];description:string;}
export interface PackMatch {id:string;compatible:boolean;reason:string;}
export interface PackCatalog {packs:MigrationPack[];compatibility:Record<string,PackMatch[]>;}
export interface Blueprint {id:string;revision:number;status:'draft'|'approved'|'rejected'|'superseded';
  snapshot_id:string;data:BlueprintData;wave_approvals:Record<string,string>;}
export interface LanguageShare { name: string; bytes: number; files: number; percent: number; }
export interface AnalysisGraph { nodes: {id:string;label:string;files:number;kind:string}[];
  edges:{from:string;to:string;type:string;inferred:boolean}[]; note:string; }
export interface DiscoverData { schema_version:number;files:number;total_lines:number; languages:Record<string,number>;
  language_bytes:Record<string,number>; language_breakdown:LanguageShare[]; modules:string[];
  graph:AnalysisGraph;findings:AnalysisFinding[];file_index:SourceFile[];methodology:string; }
export interface AnalysisFinding { id:string;file:string;line?:number|null;rule:string; severity:string;reason:string;
  kind:string; evidence:{file:string;line?:number|null;excerpt:string}; }
export interface SourceFile { path:string;language:string;module:string;bytes:number;lines:number;selected:boolean; }
export interface ScanProgress { job_id?:string;scanned:number;total:number;percent:number;
  language_bytes:Record<string,number>;languages:Record<string,number>; }
export interface DiscoverResponse {snapshot_id:string|null; data:DiscoverData|null;progress:ScanProgress|null;}

export interface AssessmentMetric {id:string;label:string;value:number;unit:string;note?:string;evidence:string;}
export interface AssessmentStrategy {id:string;module:string;strategy:string;reason:string;source:string;requires_review:boolean;}
export interface AssessmentData {status:'partial'|'completed';metrics:AssessmentMetric[];
  signals:{by_severity:Record<string,number>;heuristic_findings:number;code_files:number};
  recommendations:AssessmentStrategy[];ai_suggestions:AssessmentStrategy[];score_reason:string;
  limits:string[];confidence_score:number|null;coverage?:Record<string,any>;
}
export interface SourceSelectionResponse { snapshot_id:string;files:SourceFile[];selected_files:string[];explicit_selection:boolean; }
export interface ReviewItem { id:string;phase:string;kind:string;status:'pending'|'confirmed'|'discarded';title:string;
  comment:string;evidence:Record<string,any>;reviewed_at?:string; }
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const session = inject(AuthSessionService);
  const token = session.token;
  const publicAuth = /\/auth\/(?:login|register|config)(?:\?|$)/.test(req.url);
  const request = token && !publicAuth
    ? req.clone({setHeaders: {Authorization: `Bearer ${token}`}}) : req;
  return next(request).pipe(catchError(error => {
    // A 502/network outage is NOT an invalid session. Only an authenticated 401
    // can invalidate a token, and never one superseded by another login.
    if (!publicAuth && token && error instanceof HttpErrorResponse && error.status === 401) {
      session.clear(token);
    }
    return throwError(() => error);
  }));
};

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = '/api';
  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.base}/auth/login`, {email, password});
  }
  register(email: string, password: string, display_name: string, bootstrap_secret: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.base}/auth/register`, {email, password, display_name, bootstrap_secret});
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
  discover(pid: string): Observable<DiscoverResponse> { return this.http.get<DiscoverResponse>(`${this.base}/projects/${pid}/analysis/discover`); }
  analysisFiles(pid:string):Observable<SourceSelectionResponse> {return this.http.get<SourceSelectionResponse>(`${this.base}/projects/${pid}/analysis/files`);}
  setAnalysisSelection(pid:string,files:string[]):Observable<{selected_files:string[]}> {return this.http.put<{selected_files:string[]}>(`${this.base}/projects/${pid}/analysis/selection`,{files});}
  analysisConsent(pid:string):Observable<{approved:boolean;provider:string;snapshot_id:string}> {return this.http.get<{approved:boolean;provider:string;snapshot_id:string}>(`${this.base}/projects/${pid}/analysis/consent`);}
  setAnalysisConsent(pid:string,approved:boolean):Observable<{approved:boolean}> {return this.http.post<{approved:boolean}>(`${this.base}/projects/${pid}/analysis/consent`,{approved});}
  reviewItems(pid:string):Observable<ReviewItem[]> {return this.http.get<ReviewItem[]>(`${this.base}/projects/${pid}/analysis/reviews`);}
  reviewItem(pid:string,rid:string,status:string,comment:string):Observable<{ok:boolean}> {return this.http.patch<{ok:boolean}>(`${this.base}/projects/${pid}/analysis/reviews/${rid}`,{status,comment});}
  analysisPhase(pid:string,phase:'understand'|'assess'):Observable<{snapshot_id:string;data:Record<string,any>|null}> {return this.http.get<{snapshot_id:string;data:Record<string,any>|null}>(`${this.base}/projects/${pid}/analysis/${phase}`);}
  run(pid: string, phase: string): Observable<Run> { return this.http.post<Run>(`${this.base}/projects/${pid}/phases/${phase}`, {}); }
  blueprint(pid:string): Observable<{blueprint:Blueprint|null}> {
    return this.http.get<{blueprint:Blueprint|null}>(`${this.base}/projects/${pid}/blueprints/current`);
  }
  blueprintHistory(pid:string):Observable<Blueprint[]> {
    return this.http.get<Blueprint[]>(`${this.base}/projects/${pid}/blueprints/history`);
  }
  editBlueprint(pid:string,data:BlueprintData):Observable<Blueprint> {
    return this.http.patch<Blueprint>(`${this.base}/projects/${pid}/blueprints/current`,{data});
  }
  migrationPacks(pid:string): Observable<PackCatalog> {
    return this.http.get<PackCatalog>(`${this.base}/projects/${pid}/migration-packs`);
  }
  decideWave(pid:string,wid:string,approved:boolean): Observable<Blueprint> {
    return this.http.post<Blueprint>(`${this.base}/projects/${pid}/blueprints/current/waves/${encodeURIComponent(wid)}/decision`,{approved});
  }
  selectWave(pid:string,wid:string): Observable<Blueprint> {
    return this.http.post<Blueprint>(`${this.base}/projects/${pid}/blueprints/current/waves/${encodeURIComponent(wid)}/select`,{});
  }
  baselinePreflight(pid:string):Observable<BaselinePreflight> {
    return this.http.get<BaselinePreflight>(`${this.base}/projects/${pid}/baseline/preflight`);
  }
  baselineConsent(pid:string,approved:boolean):Observable<{execution_authorized:boolean}> {
    return this.http.post<{execution_authorized:boolean}>(`${this.base}/projects/${pid}/baseline/consent`,{approved});
  }
  baselineSuggestions(pid:string):Observable<{proposals:TestProposal[]}> {
    return this.http.post<{proposals:TestProposal[]}>(`${this.base}/projects/${pid}/baseline/suggestions`,{});
  }
  baselineReview(pid:string,id:string,approved:boolean):Observable<TestProposal> {
    return this.http.post<TestProposal>(`${this.base}/projects/${pid}/baseline/cases/${encodeURIComponent(id)}/decision`,{approved});
  }
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
