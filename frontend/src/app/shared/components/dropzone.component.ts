import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-dropzone',
  template: `
    <label
      class="flex cursor-pointer items-center justify-between gap-4 rounded-md border border-transparent px-1 py-2 text-sm transition hover:border-paper-200 hover:bg-paper-50 dark:hover:border-white/10 dark:hover:bg-white/5"
      [class.!border-accent-300]="over"
      [class.!bg-accent-50]="over"
      [class.text-accent-700]="over"
      (dragover)="onOver($event)"
      (dragleave)="over = false"
      (drop)="onDrop($event)"
    >
      <span class="font-medium text-ink-950 dark:text-paper-50">{{ over ? 'Drop the file' : 'Upload a document' }}</span>
      <span class="text-xs text-ink-600">PDF, Word, or text · up to 20 MB</span>
      <input class="sr-only" type="file" accept=".pdf,.docx,.txt,.md,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document" (change)="onPick($event)" />
    </label>
  `,
})
export class DropzoneComponent {
  @Output() fileSelected = new EventEmitter<File>();
  over = false;

  onOver(event: DragEvent): void {
    event.preventDefault();
    this.over = true;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.over = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) this.fileSelected.emit(file);
  }

  onPick(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.fileSelected.emit(file);
    input.value = '';
  }
}
