import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/** Brand assets are the original exports from Proyecto-Software-I/frontend (feat/29-branding).
 * dark = white logo for dark surfaces; light = black logo for light surfaces.
 * New screens should use this component rather than recreating the wordmark. */
@Component({
  selector: 'll-brand-logo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './brand-logo.component.html',
  host: { '[class.logo-hero]': "size === 'hero'", '[class.logo-symbol]': "variant === 'symbol'", '[class.logo-inverse]': 'inverse' },
  styleUrl: './brand-logo.component.css'
})
export class BrandLogoComponent {
  @Input() size: 'hero' | 'sidebar' = 'sidebar';
  @Input() variant: 'full' | 'symbol' = 'full';
  /** Force white artwork when rendered over an always-dark hero surface. */
  @Input() inverse = false;
}
