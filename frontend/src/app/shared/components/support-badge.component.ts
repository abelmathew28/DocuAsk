import { Component, Input } from '@angular/core';
import { NgIf } from '@angular/common';
import { SupportStatus } from '../../core/models/models';

@Component({
  selector: 'app-support-badge',
  imports: [NgIf],
  template: `
    <span
      *ngIf="status"
      class="inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] uppercase tracking-[0.12em]"
      [class.border-emerald-200]="status === 'supported'"
      [class.bg-emerald-50]="status === 'supported'"
      [class.text-emerald-800]="status === 'supported'"
      [class.border-amber-200]="status === 'partially_supported'"
      [class.bg-amber-50]="status === 'partially_supported'"
      [class.text-amber-900]="status === 'partially_supported'"
      [class.border-paper-200]="status === 'not_found'"
      [class.bg-paper-100]="status === 'not_found'"
      [class.text-ink-600]="status === 'not_found'"
    >
      {{ label }}
    </span>
  `,
})
export class SupportBadgeComponent {
  @Input() status: SupportStatus | null | undefined;

  get label(): string {
    if (this.status === 'supported') return 'Supported';
    if (this.status === 'partially_supported') return 'Partially supported';
    return 'Not found';
  }
}
