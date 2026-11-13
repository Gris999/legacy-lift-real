import { Injectable, inject } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Subscription, interval } from 'rxjs';
import { marked } from 'marked';
import { ApiService, Project, Provider, Run, Snapshot, IngestJob } from '../api/api.service';
import { StageView } from '../models/pipeline-stage';
import { ThemeService } from '../theme/theme.service';

const STAGES = [
  {id:'discover', index:'01', label:'Discover', description:'Inventario técnico', sprint:'S2', file:'inventory.md'},
  {id:'understand', index:'02', label:'Understand', description:'Arquitectura y documentación', sprint:'S2', file:'understand.md'},
  {id:'assess', index:'03', label:'Assess', description:'Riesgos y recomendaciones', sprint:'S2', file:'assessment.md'},
  {id:'plan', index:'04', label:'Plan', description:'Blueprint y wave', sprint:'S3', file:'blueprint.md'},
  {id:'baseline', index:'05', label:'Baseline', description:'Evidencia antes del cambio', sprint:'S3', file:'baseline.md'},
  {id:'modernize', index:'06', label:'Modernize', description:'Transformación en copia', sprint:'S4', file:'changes.patch'},
  {id:'verify', index:'07', label:'Verify', description:'Validación y decisión', sprint:'S4', file:'verification.md'},
] as const;

@Injectable({providedIn: 'root'})
export class WorkspaceFacade {
  private api = inject(ApiService);
  readonly themeService = inject(ThemeService);
  get theme(): string { return this.themeService.value; }
  toggleTheme(): void { this.themeService.toggle(); }
  private poller?: Subscription;
  readonly steps = STAGES;
  authenticated = !!sessionStorage.getItem('legacylift_session');
  password = '';
  passwordVisible = false;
  mobileNavOpen = false;
  projectQuery = '';
  email = '';
  displayName = '';
  registerMode = false;
  registrationOpen = false;
  bootstrapRequired = false;
  bootstrapSecret = '';
  currentUser = 'Operador';
  busy = false;
  error = '';
  notice = '';
  projects: Project[] = [];
  providers: Provider[] = [];
  selected?: Project;
  stageId = 'discover';
  artifactName = '';
  artifactContent = '';
  rendered = '';
  showCreate = false;
  showHelp = false;
  createName = '';
  createSystem = '';
  createProvider: Provider['id'] = 'demo';
  currentTab: 'overview' | 'artifacts' = 'overview';
  uploading = false;
  githubConfigured = false;
  githubLogin = '';
  githubRepos: {full_name:string;private:boolean;default_branch:string}[] = [];
  selectedRepo = '';
  snapshots: Snapshot[] = [];
  ingestJobs: IngestJob[] = [];
  private eventsAbort?: AbortController;
  private lastEventId = 0;
  editName = '';
  editSystem = '';
  showEdit = false;

  start(): void {
    this.api.authConfig().subscribe({next: v => {this.registrationOpen=v.registration_open;this.bootstrapRequired=v.bootstrap_required;}});
    if (this.authenticated) this.bootstrap();
    this.poller = interval(2500).subscribe(() => {
      if (!this.selected || !this.authenticated) return;
      this.refreshSelected(true);
      this.loadJobs(this.selected.id);
    });
  }
  stop(): void { this.poller?.unsubscribe(); this.eventsAbort?.abort(); }

  get userInitial(): string { return (this.currentUser.trim().charAt(0) || 'U').toUpperCase(); }
  get filteredProjects(): Project[] {
    const query = this.projectQuery.trim().toLocaleLowerCase();
    return query ? this.projects.filter(p => (p.name + ' ' + p.system_name).toLocaleLowerCase().includes(query)) : this.projects;
  }
  scrollToWorkspace(): void {
    this.mobileNavOpen = false;
    document.getElementById('workspace-top')?.scrollIntoView({
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
    });
  }

  get stages(): StageView[] {
    return STAGES.map(s => {
      const latest = this.latestRun(s.id);
      const status = latest?.status === 'running' ? 'running'
          : latest?.status === 'completed' ? 'completed'
          : latest?.status === 'failed' ? 'failed'
          : this.selected?.phase_ready?.[s.id] ? 'ready' : 'locked';
      return {...s, status};
    });
  }
  get activeStep() { return STAGES.find(s => s.id === this.stageId) ?? STAGES[0]; }
  get activeRun(): Run | undefined { return this.latestRun(this.stageId); }
  get completedCount(): number { return STAGES.filter(s => this.latestRun(s.id)?.status === 'completed').length; }
  get ingestRunning(): boolean { return this.ingestJobs.some(j=>j.status==='queued'||j.status==='running'); }
  get hasSource(): boolean { return !!this.selected?.snapshot_hash; }
  get planReady(): boolean { return this.latestRun('plan')?.status === 'completed' && this.selected?.plan_approved == null; }
  get decisionReady(): boolean { return this.latestRun('verify')?.status === 'completed' && !this.selected?.migration_decision; }
  get isAnyRunning(): boolean { return !!this.selected?.runs?.some(r => r.status === 'running'); }
  get stageRunnable(): boolean { return !!this.selected?.phase_ready?.[this.stageId] && !this.isAnyRunning; }
  get chosenProvider(): Provider | undefined { return this.providers.find(p => p.id === this.selected?.provider); }

  latestRun(stage: string): Run | undefined {
    return [...(this.selected?.runs || [])].reverse().find(r => r.phase === stage);
  }
  stageStatus(stage: string): string { return this.latestRun(stage)?.status || 'pending'; }
  displayStatus(status: string): string {
    return ({completed:'Completado',running:'Ejecutando',failed:'Error',ready:'Disponible',locked:'Bloqueado',pending:'Pendiente'} as Record<string,string>)[status] || status;
  }
  readableDate(value?: string): string {
    return value ? new Date(value).toLocaleString('es-BO', {dateStyle:'short',timeStyle:'short'}) : '—';
  }
  showError(err: unknown): void {
    const http = err as HttpErrorResponse;
    this.error = typeof http?.error?.detail === 'string' ? http.error.detail : http?.message || String(err);
    this.busy = false; this.uploading = false;
  }
  toast(msg: string): void { this.notice = msg; this.error = ''; }
  dismiss(): void { this.notice = ''; this.error = ''; }

  login(): void {
    if (!this.password || !this.email) return;
    this.busy = true;
    const result = this.registerMode
      ? this.api.register(this.email, this.password, this.displayName, this.bootstrapSecret)
      : this.api.login(this.email, this.password);
    result.subscribe({
      next: ({access_token}) => { sessionStorage.setItem('legacylift_session', access_token);
        this.authenticated = true; this.password = '';this.bootstrapSecret=''; this.busy = false; this.bootstrap(); },
      error: e => this.showError(e)
    });
  }
  logout(): void {
    if (this.authenticated) this.api.logout().subscribe({error: () => {}});
    sessionStorage.removeItem('legacylift_session'); this.authenticated=false;
    this.eventsAbort?.abort();this.mobileNavOpen=false;this.projects=[]; this.selected=undefined; this.artifactContent=''; this.notice='';
  }
  bootstrap(): void {
    this.api.me().subscribe({next: user => this.currentUser=user.username, error: () => this.logout()});
    this.api.providers().subscribe({next: rows => this.providers=rows, error:e=>this.showError(e)});
    this.loadProjects();
    this.refreshGithub();
  }
  loadProjects(): void {
    this.api.projects().subscribe({next: rows => {
      this.projects=rows;
      if (!this.selected && rows.length) this.select(rows[0].id);
    }, error:e=>this.showError(e)});
  }
  refreshGithub(): void {
    this.api.githubStatus().subscribe({next: state => {
      this.githubConfigured=state.configured;
      this.githubLogin=state.connection?.github_login || '';
      if (this.githubLogin) this.api.githubRepos().subscribe({next: rows=>this.githubRepos=rows});
    }});
  }
  connectGithub(): void {
    this.api.githubConnect().subscribe({next:r=>window.location.assign(r.url),error:e=>this.showError(e)});
  }
  disconnectGithub(): void {
    this.api.githubDisconnect().subscribe({next:()=>{this.githubLogin='';this.githubRepos=[];this.toast('GitHub desconectado.');},error:e=>this.showError(e)});
  }
  editProject(): void {
    if (!this.selected) return;
    this.editName=this.selected.name;this.editSystem=this.selected.system_name;this.showEdit=true;
  }
  saveProject(): void {
    if (!this.selected) return;
    const pid=this.selected.id;
    this.api.rename(pid,this.editName,this.editSystem).subscribe({next:()=>{
      this.showEdit=false;this.refreshSelected();this.loadProjects();this.toast('Proyecto actualizado.');
    },error:e=>this.showError(e)});
  }
  create(): void {
    if (this.createName.trim().length<3 || this.createSystem.trim().length<2) return;
    this.busy=true;
    this.api.create(this.createName.trim(), this.createSystem.trim(), this.createProvider).subscribe({
      next: p => { this.busy=false; this.showCreate=false; this.createName=''; this.createSystem='';
        this.projects=[p,...this.projects]; this.select(p.id); this.toast('Proyecto creado. Sube el ZIP para comenzar.'); },
      error:e=>this.showError(e)
    });
  }
  select(pid: string): void {
    this.eventsAbort?.abort();this.lastEventId=0;this.ingestJobs=[];
    this.selected = undefined; this.artifactContent=''; this.artifactName=''; this.stageId='discover';
    this.api.project(pid).subscribe({next:p=>{this.selected=p; this.pickFirstArtifact(); this.loadSnapshots(pid);this.loadJobs(pid);this.connectEvents(pid);},error:e=>this.showError(e)});
  }
  refreshSelected(silent=false): void {
    if (!this.selected) return;
    const pid = this.selected.id;
    this.api.project(pid).subscribe({next: updated => {
      if (!this.selected || this.selected.id !== pid) return;
      const was = this.selected.runs?.length ?? 0;
      const hadRunning = this.selected.runs?.some(x=>x.status==='running') ?? false;
      const sourceChanged=updated.active_snapshot_id!==this.selected.active_snapshot_id;
      this.selected=updated;
      if (!silent || sourceChanged) { this.loadSnapshots(pid);this.loadJobs(pid); }
      if (sourceChanged) this.pickFirstArtifact();
      if (hadRunning && !this.isAnyRunning) {
        if (this.activeRun?.status === 'completed') {
          this.toast('Fase completada; consulta el artefacto generado.');
          this.openArtifact(this.activeStep.file);
        } else if (this.activeRun?.status === 'failed') {
          this.error=this.activeRun.error || 'La operación falló';
        }
      }
      if (!silent || was===0) this.loadProjects();
    },error:e=>{if(!silent)this.showError(e)}});
  }
  pickFirstArtifact(): void {
    const arr = this.selected?.artifacts || [];
    if (arr.includes('inventory.md')) this.openArtifact('inventory.md');
    else if (arr.length) this.openArtifact(arr[0]);
  }
  chooseStage(id: string): void {
    this.stageId=id;
    const step=STAGES.find(x=>x.id===id);
    if (step && this.selected?.artifacts?.includes(step.file)) this.openArtifact(step.file);
  }
  loadJobs(pid: string): void {
    this.api.jobs(pid).subscribe({next:items=>{if(this.selected?.id===pid){
      const previouslyRunning=this.ingestRunning;
      this.ingestJobs=items;
      if (previouslyRunning && !this.ingestRunning) {
        this.refreshSelected();
        this.toast(items[0]?.status==='completed'?'Código importado y escaneado.':'La ingesta terminó; revisa su estado.');
      }
    }}});
  }
  retryJob(jid: string): void {
    if (!this.selected) return;
    this.api.retry(this.selected.id,jid).subscribe({next:()=>{
      this.toast('Ingesta reintentada.');this.loadJobs(this.selected!.id);
    },error:e=>this.showError(e)});
  }
  cancelJob(jid: string): void {
    if (!this.selected) return;
    this.api.cancel(this.selected.id,jid).subscribe({next:()=>{
      this.toast('Trabajo cancelado.');this.loadJobs(this.selected!.id);
    },error:e=>this.showError(e)});
  }
  private async connectEvents(pid: string): Promise<void> {
    this.eventsAbort?.abort();
    const controller=new AbortController();this.eventsAbort=controller;
    try {
      const token=sessionStorage.getItem('legacylift_session');
      if (!token) return;
      const response=await fetch(`/api/projects/${pid}/events?after=${this.lastEventId}`, {
        headers:{Authorization:`Bearer ${token}`},signal:controller.signal,cache:'no-store'
      });
      if (!response.ok || !response.body) return; // Polling remains as fallback.
      const reader=response.body.getReader();const decoder=new TextDecoder();let buffer='';
      while(!controller.signal.aborted) {
        const {value,done}=await reader.read();if(done) break;
        buffer+=decoder.decode(value,{stream:true}).replace(/\r\n/g,'\n');
        const frames=buffer.split('\n\n');buffer=frames.pop() || '';
        for(const frame of frames) {
          const id=frame.match(/^id: (\d+)/m);
          if(id) this.lastEventId=Math.max(this.lastEventId,Number(id[1]));
          if(frame.includes('event: update') && this.selected?.id===pid) {
            this.refreshSelected(true);this.loadJobs(pid);
          }
        }
      }
    } catch(e) { if(!controller.signal.aborted) { /* polling fallback */ } }
  }
  loadSnapshots(pid: string): void {
    this.api.snapshots(pid).subscribe({next:items=>{if(this.selected?.id===pid)this.snapshots=items;}});
  }
  activateSnapshot(sid: string): void {
    if (!this.selected || sid===this.selected.active_snapshot_id) return;
    const pid=this.selected.id;
    this.busy=true;
    this.api.activateSnapshot(pid,sid).subscribe({next:()=>{
      this.busy=false;this.artifactContent='';this.refreshSelected();this.toast('Snapshot activado. Análisis anteriores invalidado.');
    },error:e=>this.showError(e)});
  }
  importRepository(): void {
    if (!this.selected || !this.selectedRepo || this.uploading) return;
    const pid=this.selected.id;this.uploading=true;
    this.api.importGit(pid,this.selectedRepo).subscribe({next:job=>{
      this.uploading=false;this.toast(`Importación ${job.id.slice(0,8)} en cola. Sigue el progreso.`);this.loadJobs(pid);
    },error:e=>this.showError(e)});
  }
  upload(event: Event): void {
    const input=event.target as HTMLInputElement;
    const file=input.files?.[0];
    if (!file || !this.selected) return;
    this.uploading=true;
    this.api.upload(this.selected.id,file).subscribe({
      next: job=>{this.uploading=false;this.toast(`Ingesta ${job.id.slice(0,8)} iniciada.`);this.loadJobs(this.selected!.id);},
      error:e=>this.showError(e)
    });
    input.value='';
  }
  loadDemo(): void {
    if (!this.selected || this.uploading) return;
    const pid = this.selected.id; this.uploading = true;
    this.api.demoZip().subscribe({
      next: blob => {
        const file = new File([blob], 'legacylift-demo.zip', {type: 'application/zip'});
        this.api.upload(pid, file).subscribe({
          next: job => { this.uploading = false; this.toast(`Ejemplo: ingesta ${job.id.slice(0,8)} en ejecución.`);this.loadJobs(pid); },
          error: e => this.showError(e)
        });
      }, error: e => this.showError(e)
    });
  }
  run(): void {
    if (!this.selected || !this.stageRunnable) return;
    this.busy=true;
    this.api.run(this.selected.id,this.stageId).subscribe({
      next:()=>{this.busy=false; this.toast('Ejecución iniciada. La interfaz actualizará el estado.');this.refreshSelected();},
      error:e=>this.showError(e)
    });
  }
  planDecision(approved:boolean): void {
    if (!this.selected) return;
    this.api.plan(this.selected.id,approved).subscribe({
      next:()=>{this.toast(approved?'Plan aprobado. Ya puedes preparar el baseline.':'Plan rechazado.');this.refreshSelected();},
      error:e=>this.showError(e)
    });
  }
  migrationDecision(approved:boolean): void {
    if (!this.selected) return;
    this.api.decision(this.selected.id,approved).subscribe({
      next:()=>{this.toast(approved?'Migración aprobada y lista para exportar.':'Migración rechazada. Candidato descartado.');this.refreshSelected();},
      error:e=>this.showError(e)
    });
  }
  openArtifact(filename:string): void {
    if (!this.selected) return;
    this.artifactName=filename;
    this.api.artifact(this.selected.id,filename).subscribe({next: text=>{
      this.artifactContent=text;
      // Angular sanitizes the [innerHTML] binding; never bypass its sanitizer.
      this.rendered = filename.endsWith('.md') ? String(marked.parse(text)) : '';
    }, error:e=>this.showError(e)});
  }
  copyArtifact(): void { if (this.artifactContent) navigator.clipboard.writeText(this.artifactContent)
      .then(()=>this.toast('Contenido copiado')).catch(()=>this.toast('No se pudo copiar; selecciona el texto manualmente.')); }
  download(): void {
    if (!this.selected) return;
    this.api.export(this.selected.id).subscribe({next: blob=>{
      const url=URL.createObjectURL(blob);
      const el=document.createElement('a');el.href=url;el.download='legacylift-evidencias.zip';el.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    }, error:e=>this.showError(e)});
  }
}
