import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent } from '../../../shared/ui';

@Component({
  selector: 'll-workspace-topbar',
  standalone: true,
  imports: [CommonModule, IconComponent],
  templateUrl: './workspace-topbar.component.html',
  styleUrl: './workspace-topbar.component.css'
})
export class WorkspaceTopbarComponent {
  readonly vm = inject(WorkspaceFacade);
}
