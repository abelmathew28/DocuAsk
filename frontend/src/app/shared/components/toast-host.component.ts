import { Component, inject } from '@angular/core';
import { NgFor } from '@angular/common';
import { ToastService } from '../../core/services/toast.service';

@Component({
  selector: 'app-toast-host',
  imports: [NgFor],
  template: `
    <div class="pointer-events-none fixed right-4 top-4 z-[80] flex w-[min(100%-2rem,22rem)] flex-col gap-2" aria-live="polite">
      <div
        *ngFor="let toast of toasts()"
        class="dialog-in pointer-events-auto border border-paper-200 bg-white px-4 py-3 text-sm dark:border-white/10 dark:bg-ink-900"
        [class.text-red-700]="toast.type === 'error'"
        [class.text-ink-950]="toast.type !== 'error'"
      >
        {{ toast.message }}
      </div>
    </div>
  `,
})
export class ToastHostComponent {
  private readonly toast = inject(ToastService);
  readonly toasts = this.toast.toasts;
}
