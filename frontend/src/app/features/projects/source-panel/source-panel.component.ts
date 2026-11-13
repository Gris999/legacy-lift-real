import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, StatusBadgeComponent, SectionHeadingComponent } from '../../../shared/ui';

@Component({
  selector: 'll-source-panel',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent, ButtonDirective, StatusBadgeComponent, SectionHeadingComponent],
  templateUrl: './source-panel.component.html',
  styleUrl: './source-panel.component.css'
})
export class SourcePanelComponent {
  readonly vm = inject(WorkspaceFacade);
}
