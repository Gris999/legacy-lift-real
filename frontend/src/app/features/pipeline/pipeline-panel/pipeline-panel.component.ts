import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, SectionHeadingComponent } from '../../../shared/ui';
import { StageCardComponent } from '../stage-card/stage-card.component';

@Component({
  selector: 'll-pipeline-panel',
  standalone: true,
  imports: [CommonModule, IconComponent, SectionHeadingComponent, StageCardComponent],
  templateUrl: './pipeline-panel.component.html',
  styleUrl: './pipeline-panel.component.css'
})
export class PipelinePanelComponent {
  readonly vm = inject(WorkspaceFacade);
}
