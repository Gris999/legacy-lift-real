import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { ButtonDirective, IconComponent } from '../../../shared/ui';

@Component({selector:'ll-migration-review',standalone: true,imports:[CommonModule,ButtonDirective,IconComponent],
  templateUrl: './migration-review.component.html',styleUrl: './migration-review.component.css'})
export class MigrationReviewComponent {readonly vm=inject(WorkspaceFacade);}
