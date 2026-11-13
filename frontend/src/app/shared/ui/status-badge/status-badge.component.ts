import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { IconComponent } from '../icon/icon.component';

/** Shared accessible status semantics for jobs, phases, connections and decisions. */
@Component({
  selector: 'll-status-badge',
  standalone: true,
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './status-badge.component.html',
  styleUrl: './status-badge.component.css'
})
export class StatusBadgeComponent {
  @Input() status = 'pending';
  @Input() label = '';
  get tone(): string {
    if (['completed', 'approved', 'active', 'success', 'connected'].includes(this.status)) return 'success';
    if (['failed', 'rejected', 'error'].includes(this.status)) return 'danger';
    if (['running', 'queued', 'ready'].includes(this.status)) return 'info';
    return 'neutral';
  }
  get icon(): string {
    return ({ success:'check_circle', danger:'error', info:'progress_activity', neutral:'schedule' } as Record<string,string>)[this.tone];
  }
  get text(): string {
    return ({completed:'Completado', approved:'Aprobado', active:'Activo', success:'Correcto', connected:'Conectado',
      failed:'Error', rejected:'Rechazado', error:'Error', running:'En ejecución', queued:'En cola', ready:'Disponible',
      locked:'Bloqueado', canceled:'Cancelado', pending:'Pendiente'} as Record<string,string>)[this.status] || this.status;
  }
}
