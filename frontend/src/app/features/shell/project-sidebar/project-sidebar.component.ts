import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, BrandLogoComponent } from '../../../shared/ui';

@Component({
  selector: 'll-project-sidebar',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent, ButtonDirective, BrandLogoComponent],
  templateUrl: './project-sidebar.component.html',
  styleUrl: './project-sidebar.component.css'
})
export class ProjectSidebarComponent {
  readonly vm = inject(WorkspaceFacade);
}
