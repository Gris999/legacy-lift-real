import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent } from '../../../shared/ui';
import { OrganizationConsoleComponent } from '../../organizations/organization-console/organization-console.component';

@Component({
  selector: 'll-workspace-topbar',
  standalone: true,
  imports: [CommonModule, IconComponent, OrganizationConsoleComponent],
  templateUrl: './workspace-topbar.component.html',
  styleUrl: './workspace-topbar.component.css'
})
export class WorkspaceTopbarComponent {
  readonly vm = inject(WorkspaceFacade);
}
