import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, StatusBadgeComponent } from '../../../shared/ui';

@Component({
  selector: 'll-phase-actions',
  standalone: true,
  imports: [CommonModule, IconComponent, ButtonDirective, StatusBadgeComponent],
  templateUrl: './phase-actions.component.html',
  styleUrl: './phase-actions.component.css'
})
export class PhaseActionsComponent {
  readonly vm = inject(WorkspaceFacade);
}
