import { Component, Input } from '@angular/core';
import { NgIf } from '@angular/common';
import { DocumentStatus } from '../../core/models/models';

@Component({
  selector: 'app-status-badge',
  imports: [NgIf],
  template: `
    <span class="text-[11px] font-medium uppercase tracking-[0.12em] text-ink-600" [class]="tone">
      <span *ngIf="status === 'processing' || status === 'uploading'" class="processing-dot">· </span>{{ label }}
    </span>
  `,
})
export class StatusBadgeComponent {
  @Input() status: DocumentStatus = 'processing';
  @Input() stage: string | null = null;

  get label(): string {
    if ((this.status === 'processing' || this.status === 'uploading') && this.stage) {
      return this.stage.replace(/_/g, ' ');
    }
    return this.status;
  }

  get tone(): string {
    switch (this.status) {
      case 'ready':
        return 'text-ink-950 dark:text-paper-50';
      case 'failed':
        return 'text-red-800 dark:text-red-200';
      case 'uploading':
        return 'text-ink-600';
      default:
        return 'text-ink-600';
    }
  }
}
