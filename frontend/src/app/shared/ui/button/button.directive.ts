import { Directive, Input } from '@angular/core';

/** Consistent button sizing/variants; never overrides native disabled, type or click behavior. */
@Directive({
  selector: 'button[llButton], a[llButton]',
  standalone: true,
  host: {
    class: 'll-btn',
    '[class.ll-btn-primary]': 'variant === "primary"',
    '[class.ll-btn-secondary]': 'variant === "secondary"',
    '[class.ll-btn-ghost]': 'variant === "ghost"',
    '[class.ll-btn-danger]': 'variant === "danger"',
    '[class.ll-btn-sm]': 'size === "sm"',
    '[class.ll-btn-block]': 'block'
  }
})
export class ButtonDirective {
  @Input() variant: 'primary' | 'secondary' | 'ghost' | 'danger' = 'secondary';
  @Input() size: 'sm' | 'md' = 'md';
  @Input() block = false;
}
