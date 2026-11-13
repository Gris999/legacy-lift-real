import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

/** Presentational Material Symbol. Accessible name belongs to its parent action. */
@Component({
  selector: 'll-icon',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './icon.component.html',
  styleUrl: './icon.component.css',
  host: { class: 'll-icon', '[class.icon-small]': 'size === "sm"', '[class.icon-large]': 'size === "lg"' }
})
export class IconComponent {
  @Input({ required: true }) name = 'circle';
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
}
