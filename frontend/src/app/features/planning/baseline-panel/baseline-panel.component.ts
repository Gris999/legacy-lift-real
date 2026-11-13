import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { ButtonDirective, IconComponent, SectionHeadingComponent, StatusBadgeComponent } from '../../../shared/ui';

@Component({selector:'ll-baseline-panel', standalone: true,
  imports:[CommonModule,ButtonDirective,IconComponent,SectionHeadingComponent,StatusBadgeComponent],
  templateUrl: './baseline-panel.component.html', styleUrl: './baseline-panel.component.css'})
export class BaselinePanelComponent { readonly vm=inject(WorkspaceFacade); }
