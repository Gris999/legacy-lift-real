import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AnalysisGraph } from '../../../core/api/api.service';
import { IconComponent } from '../../../shared/ui';

interface PositionedNode {id:string;label:string;files:number;x:number;y:number;}
interface PositionedEdge {from:string;to:string;x1:number;y1:number;x2:number;y2:number;}
@Component({selector:'ll-architecture-graph',standalone: true,imports:[CommonModule,IconComponent],
  templateUrl: './architecture-graph.component.html',styleUrl: './architecture-graph.component.css'})
export class ArchitectureGraphComponent implements OnChanges {
  @Input({required:true}) graph!:AnalysisGraph;
  nodes:PositionedNode[]=[];edges:PositionedEdge[]=[];active?:PositionedNode;
  ngOnChanges():void {
    const raw=this.graph?.nodes?.slice(0,28)||[];
    this.nodes=raw.map((n,i)=>({id:n.id,label:n.label,files:n.files,
      x:280+210*Math.cos(i*2*Math.PI/Math.max(raw.length,1)-Math.PI/2),
      y:240+190*Math.sin(i*2*Math.PI/Math.max(raw.length,1)-Math.PI/2)}));
    const map=new Map(this.nodes.map(n=>[n.id,n]));
    this.edges=(this.graph?.edges||[]).flatMap(e=>{
      const a=map.get(e.from),b=map.get(e.to);return a&&b?[{from:e.from,to:e.to,x1:a.x,y1:a.y,x2:b.x,y2:b.y}]:[];
    });
    this.active=this.nodes[0];
  }
  select(node:PositionedNode):void {this.active=node;}
  neighbors():PositionedNode[] {
    return this.nodes.filter(n=>this.edges.some(e=>(e.from===this.active?.id&&e.to===n.id)||(e.to===this.active?.id&&e.from===n.id)));
  }
}
