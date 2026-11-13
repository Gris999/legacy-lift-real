import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, SectionHeadingComponent } from '../../../shared/ui';

@Component({selector:'ll-review-queue',standalone: true,
 imports:[CommonModule,FormsModule,IconComponent,ButtonDirective,SectionHeadingComponent],
 templateUrl: './review-queue.component.html',styleUrl: './review-queue.component.css'})
export class ReviewQueueComponent {readonly vm=inject(WorkspaceFacade);}
