import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, MetricCardComponent, NoticeComponent } from '../../../shared/ui';
import { SourcePanelComponent } from '../source-panel/source-panel.component';
import { PipelinePanelComponent } from '../../pipeline/pipeline-panel/pipeline-panel.component';
import { PhaseActionsComponent } from '../../pipeline/phase-actions/phase-actions.component';
import { AssessmentOverviewComponent } from '../../analysis/assessment-overview/assessment-overview.component';
import { AnalysisControlsComponent } from '../../analysis/analysis-controls/analysis-controls.component';
import { ReviewQueueComponent } from '../../analysis/review-queue/review-queue.component';
import { DiscoverOverviewComponent } from '../../analysis/discover-overview/discover-overview.component';
import { BaselinePanelComponent } from '../../planning/baseline-panel/baseline-panel.component';
import { MigrationPacksComponent } from '../../planning/migration-packs/migration-packs.component';
import { BlueprintEditorComponent } from '../../planning/blueprint-editor/blueprint-editor.component';
import { ArtifactsPanelComponent } from '../../artifacts/artifacts-panel/artifacts-panel.component';

@Component({
  selector: 'll-project-dashboard',
  standalone: true,
  imports: [CommonModule, IconComponent, ButtonDirective, MetricCardComponent, NoticeComponent, SourcePanelComponent, PipelinePanelComponent, PhaseActionsComponent, ArtifactsPanelComponent, DiscoverOverviewComponent, AnalysisControlsComponent, ReviewQueueComponent, AssessmentOverviewComponent, BlueprintEditorComponent, MigrationPacksComponent, BaselinePanelComponent],
  templateUrl: './project-dashboard.component.html',
  styleUrl: './project-dashboard.component.css'
})
export class ProjectDashboardComponent {
  readonly vm = inject(WorkspaceFacade);
  readonly workspaceTabs = [
    {id:'source',label:'Fuente',icon:'upload_file'},
    {id:'discover',label:'Discover',icon:'manage_search'},
    {id:'understand',label:'Understand',icon:'account_tree'},
    {id:'assess',label:'Assess',icon:'monitor_heart'},
    {id:'plan',label:'Plan',icon:'schema'},
    {id:'baseline',label:'Baseline',icon:'fact_check'},
    {id:'modernize',label:'Modernize',icon:'auto_fix_high'},
    {id:'verify',label:'Verify',icon:'verified'},
    {id:'evidence',label:'Evidencias',icon:'folder_open'}
  ] as const;
}
