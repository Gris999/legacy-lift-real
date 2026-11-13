import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { LanguageShare } from '../../../core/api/api.service';
import { IconComponent, SectionHeadingComponent } from '../../../shared/ui';
import { ArchitectureGraphComponent } from '../architecture-graph/architecture-graph.component';

@Component({
  selector:'ll-discover-overview', standalone: true,
  imports:[CommonModule,IconComponent,SectionHeadingComponent,ArchitectureGraphComponent],
  templateUrl: './discover-overview.component.html',
  styleUrl: './discover-overview.component.css'
})
export class DiscoverOverviewComponent {
  readonly vm=inject(WorkspaceFacade);
  private readonly palette:Record<string,string> = {
    Python:'#3572a5',TypeScript:'#3178c6',JavaScript:'#d5b900',Java:'#b07219',
    PHP:'#777bb4',COBOL:'#9060b3','C#':'#178600',Go:'#00add8',CSS:'#563d7c',HTML:'#e34c26',SQL:'#64748b'
  };
  get shares():LanguageShare[] {
    if(this.vm.discoverData) return this.vm.discoverData.language_breakdown;
    const progress=this.vm.scanProgress;
    if(!progress) return [];
    const total=Object.values(progress.language_bytes).reduce((a,b)=>a+b,0);
    return Object.entries(progress.language_bytes).sort((a,b)=>b[1]-a[1]).map(([name,bytes])=>({
      name,bytes,files:progress.languages[name]||0,percent:total?100*bytes/total:0
    }));
  }
  color(name:string):string {return this.palette[name] || '#77808f';}
  get progress():number {return this.vm.scanProgress?.percent||0;}
}
