import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

@Component({
  selector: 'll-section-heading',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './section-heading.component.html',
  styleUrl: './section-heading.component.css',
  imports: [CommonModule]
})
export class SectionHeadingComponent {
  @Input() eyebrow = '';
  @Input({required:true}) title = '';
  @Input() description = '';
}
