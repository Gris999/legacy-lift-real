import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { ButtonDirective, IconComponent } from '../../../shared/ui';
@Component({selector:'ll-verify-result',standalone: true,imports:[CommonModule,ButtonDirective,IconComponent],
  templateUrl: './verify-result.component.html',styleUrl: './verify-result.component.css'})
export class VerifyResultComponent {readonly vm=inject(WorkspaceFacade);}
