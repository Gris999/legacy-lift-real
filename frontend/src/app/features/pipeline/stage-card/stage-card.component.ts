import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { IconComponent, StatusBadgeComponent } from '../../../shared/ui';

import { StageView } from '../../../core/models/pipeline-stage';

@Component({
  standalone: true,
  selector: 'll-stage-card',
  imports: [CommonModule, IconComponent, StatusBadgeComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './stage-card.component.html',
  styleUrl: './stage-card.component.css'
})
export class StageCardComponent {
  @Input({required:true}) stage!: StageView;
  @Input() active = false;
  @Output() selected = new EventEmitter<string>();
}
