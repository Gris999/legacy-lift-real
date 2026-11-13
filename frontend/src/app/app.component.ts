import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { WorkspaceFacade } from './core/state/workspace.facade';
import { AuthPageComponent } from './features/auth/auth-page/auth-page.component';
import { WorkspaceShellComponent } from './features/shell/workspace-shell/workspace-shell.component';
import { ProjectDialogsComponent } from './features/projects/project-dialogs/project-dialogs.component';

/** Composition root. Business state and side effects belong to WorkspaceFacade. */
@Component({
  selector: 'll-root',
  standalone: true,
  imports: [CommonModule, AuthPageComponent, WorkspaceShellComponent, ProjectDialogsComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent implements OnInit, OnDestroy {
  readonly vm = inject(WorkspaceFacade);
  ngOnInit(): void { this.vm.start(); }
  ngOnDestroy(): void { this.vm.stop(); }
}
