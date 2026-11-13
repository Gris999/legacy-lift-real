import { CommonModule } from '@angular/common';
import { Component,inject } from '@angular/core';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { ButtonDirective, IconComponent, SectionHeadingComponent, StatusBadgeComponent } from '../../../shared/ui';

@Component({selector:'ll-migration-packs',standalone: true,
  imports:[CommonModule,ButtonDirective,IconComponent,SectionHeadingComponent,StatusBadgeComponent],
  templateUrl: './migration-packs.component.html', styleUrl: './migration-packs.component.css'})
export class MigrationPacksComponent {readonly vm=inject(WorkspaceFacade);}
