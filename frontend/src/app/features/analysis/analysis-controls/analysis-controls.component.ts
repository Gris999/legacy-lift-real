import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, SectionHeadingComponent } from '../../../shared/ui';

@Component({selector:'ll-analysis-controls',standalone: true,
  imports:[CommonModule,FormsModule,IconComponent,ButtonDirective,SectionHeadingComponent],
  templateUrl: './analysis-controls.component.html',styleUrl: './analysis-controls.component.css'})
export class AnalysisControlsComponent {readonly vm=inject(WorkspaceFacade);}
