import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, DialogComponent } from '../../../shared/ui';

@Component({
  selector: 'll-project-dialogs',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent, ButtonDirective, DialogComponent],
  templateUrl: './project-dialogs.component.html',
  styleUrl: './project-dialogs.component.css'
})
export class ProjectDialogsComponent {
  readonly vm = inject(WorkspaceFacade);
}
