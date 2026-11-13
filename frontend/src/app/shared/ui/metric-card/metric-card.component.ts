import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IconComponent } from '../icon/icon.component';

/** Reusable metric with optional accessible numeric progress indicator. */
@Component({
  selector: 'll-metric-card',
  standalone: true,
  imports: [CommonModule, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './metric-card.component.html',
  styleUrl: './metric-card.component.css'
})
export class MetricCardComponent {
  @Input({required: true}) title = '';
  @Input({required: true}) value = '';
  @Input() icon = 'analytics';
  @Input() suffix = '';
  @Input() detail = '';
  @Input() progress: number | null = null;
  @Input() compact = false;
}
