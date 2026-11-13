import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, StatusBadgeComponent, SectionHeadingComponent } from '../../../shared/ui';

@Component({
  selector: 'll-artifacts-panel',
  standalone: true,
  imports: [CommonModule, IconComponent, ButtonDirective, StatusBadgeComponent, SectionHeadingComponent],
  templateUrl: './artifacts-panel.component.html',
  styleUrl: './artifacts-panel.component.css'
})
export class ArtifactsPanelComponent {
  readonly vm = inject(WorkspaceFacade);
}
