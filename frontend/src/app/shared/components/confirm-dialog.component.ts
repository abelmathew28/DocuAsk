import { Component, EventEmitter, Input, Output } from '@angular/core';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-confirm-dialog',
  imports: [NgIf],
  template: `
    <div *ngIf="open" class="fixed inset-0 z-[70] flex items-center justify-center p-4">
      <button class="absolute inset-0 bg-ink-950/40" type="button" aria-label="Close dialog" (click)="cancel.emit()"></button>
      <div role="dialog" aria-modal="true" class="dialog-in relative w-full max-w-md border border-paper-200 bg-paper-50 p-6 dark:border-white/10 dark:bg-ink-950">
        <h2 class="font-display text-2xl text-ink-950 dark:text-paper-50">{{ title }}</h2>
        <p class="mt-2 text-sm leading-6 text-ink-600">{{ message }}</p>
        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="btn-quiet" (click)="cancel.emit()">Cancel</button>
          <button type="button" class="rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800" (click)="confirm.emit()">
            {{ confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  `,
})
export class ConfirmDialogComponent {
  @Input() open = false;
  @Input() title = 'Are you sure?';
  @Input() message = 'This action cannot be undone.';
  @Input() confirmLabel = 'Delete';
  @Output() confirm = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();
}
