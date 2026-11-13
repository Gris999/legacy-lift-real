import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, SectionHeadingComponent } from '../../../shared/ui';

@Component({selector:'ll-assessment-overview',standalone: true,
  imports:[CommonModule,IconComponent,SectionHeadingComponent],
  templateUrl: './assessment-overview.component.html',styleUrl: './assessment-overview.component.css'})
export class AssessmentOverviewComponent {
  readonly vm=inject(WorkspaceFacade);
  get severities():{name:string;value:number;percent:number}[] {
    const groups=this.vm.assessmentData?.signals.by_severity || {};
    const total=Object.values(groups).reduce((a,b)=>a+b,0);
    return Object.entries(groups).map(([name,value])=>({name,value,percent:total?value*100/total:0}));
  }
}
