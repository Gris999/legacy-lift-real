import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, MetricCardComponent, NoticeComponent } from '../../../shared/ui';
import { SourcePanelComponent } from '../source-panel/source-panel.component';
import { PipelinePanelComponent } from '../../pipeline/pipeline-panel/pipeline-panel.component';
import { PhaseActionsComponent } from '../../pipeline/phase-actions/phase-actions.component';
import { ArtifactsPanelComponent } from '../../artifacts/artifacts-panel/artifacts-panel.component';

@Component({
  selector: 'll-project-dashboard',
  standalone: true,
  imports: [CommonModule, IconComponent, ButtonDirective, MetricCardComponent, NoticeComponent, SourcePanelComponent, PipelinePanelComponent, PhaseActionsComponent, ArtifactsPanelComponent],
  templateUrl: './project-dashboard.component.html',
  styleUrl: './project-dashboard.component.css'
})
export class ProjectDashboardComponent {
  readonly vm = inject(WorkspaceFacade);
}
