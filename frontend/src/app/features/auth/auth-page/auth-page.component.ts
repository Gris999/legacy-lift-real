import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { WorkspaceFacade } from '../../../core/state/workspace.facade';
import { IconComponent, ButtonDirective, NoticeComponent, BrandLogoComponent } from '../../../shared/ui';

@Component({
  selector: 'll-auth-page',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent, ButtonDirective, NoticeComponent, BrandLogoComponent],
  templateUrl: './auth-page.component.html',
  styleUrl: './auth-page.component.css'
})
export class AuthPageComponent {
  readonly vm = inject(WorkspaceFacade);
}
