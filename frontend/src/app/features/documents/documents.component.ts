import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { DocumentService } from '../../core/services/document.service';
import { ConversationService } from '../../core/services/conversation.service';
import { DocumentItem, DocumentStatus } from '../../core/models/models';
import { DropzoneComponent } from '../../shared/components/dropzone.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge.component';
import { ConfirmDialogComponent } from '../../shared/components/confirm-dialog.component';
import { EmptyStateComponent } from '../../shared/components/empty-state.component';
import { ToastService } from '../../core/services/toast.service';
import { formatBytes, relativeTime, explainDocumentError } from '../../shared/utils';
import { documentBrief, starterQuestions } from '../../shared/document-starters';

@Component({
  selector: 'app-documents',
  imports: [
    NgIf,
    NgFor,
    FormsModule,
    DropzoneComponent,
    StatusBadgeComponent,
    ConfirmDialogComponent,
    EmptyStateComponent,
  ],
  templateUrl: './documents.component.html',
})
export class DocumentsComponent implements OnInit, OnDestroy {
  private readonly api = inject(DocumentService);
  private readonly conversations = inject(ConversationService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly toast = inject(ToastService);
  private poll?: ReturnType<typeof setInterval>;

  items = signal<DocumentItem[]>([]);
  query = '';
  status: DocumentStatus | '' = '';
  sort = 'created_at';
  view: 'list' | 'grid' = 'list';
  uploading = false;
  pendingDelete: DocumentItem | null = null;
  renaming: DocumentItem | null = null;
  renameValue = '';
  starredOnly = false;
  inspecting: DocumentItem | null = null;
  formatBytes = formatBytes;
  relativeTime = relativeTime;
  explainError = explainDocumentError;

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const id = params.get('id');
      if (id) {
        this.openById(id);
      }
    });
    this.route.queryParamMap.subscribe((params) => {
      const q = params.get('q');
      if (q) this.query = q;
      this.reload();
    });
    this.poll = setInterval(() => {
      if (this.items().some((doc) => doc.status === 'processing' || doc.status === 'uploading')) {
        this.reload();
      }
    }, 3000);
  }

  ngOnDestroy(): void {
    if (this.poll) clearInterval(this.poll);
  }

  reload(): void {
    this.api
      .list({ q: this.query, status: this.status, sort: this.sort, starred: this.starredOnly || undefined })
      .subscribe((items) => {
        this.items.set(items);
        if (this.inspecting) {
          this.inspecting = items.find((item) => item.id === this.inspecting?.id) || null;
        }
        const id = this.route.snapshot.paramMap.get('id');
        if (id && !this.inspecting) {
          this.inspecting = items.find((item) => item.id === id) || null;
        }
      });
  }

  openById(id: string): void {
    const found = this.items().find((item) => item.id === id);
    if (found) {
      this.inspecting = found;
      return;
    }
    this.api.get(id).subscribe({
      next: (doc) => (this.inspecting = doc),
      error: () => this.toast.success('Document not found.'),
    });
  }

  openDetails(doc: DocumentItem): void {
    this.inspecting = doc;
    void this.router.navigate(['/app/documents', doc.id]);
  }

  closeDetails(): void {
    this.inspecting = null;
    void this.router.navigate(['/app/documents']);
  }

  typeBadge(doc: DocumentItem): string {
    return (doc.document_type || 'pdf').toUpperCase();
  }

  upload(file: File): void {
    this.uploading = true;
    this.api.upload(file).subscribe({
      next: () => {
        this.uploading = false;
        this.toast.success('Document uploaded. Processing has started.');
        this.reload();
      },
      error: () => (this.uploading = false),
    });
  }

  ask(doc: DocumentItem, question?: string): void {
    this.conversations.create({ document_id: doc.id, title: question?.slice(0, 48) }).subscribe((conversation) => {
      void this.router.navigate(['/app/ask', conversation.id], question ? { state: { draft: question } } : undefined);
    });
  }

  confirmDelete(doc: DocumentItem): void {
    this.pendingDelete = doc;
  }

  delete(): void {
    if (!this.pendingDelete) return;
    this.api.delete(this.pendingDelete.id).subscribe(() => {
      this.toast.success('Document deleted.');
      this.pendingDelete = null;
      this.inspecting = null;
      void this.router.navigate(['/app/documents']);
      this.reload();
    });
  }

  startRename(doc: DocumentItem): void {
    this.renaming = doc;
    this.renameValue = doc.name;
  }

  saveRename(): void {
    if (!this.renaming || !this.renameValue.trim()) return;
    this.api.rename(this.renaming.id, this.renameValue.trim()).subscribe(() => {
      this.renaming = null;
      this.reload();
    });
  }

  toggleStar(doc: DocumentItem): void {
    this.api.star(doc.id, !doc.is_starred).subscribe(() => this.reload());
  }

  download(doc: DocumentItem): void {
    this.api.download(doc.id, doc.original_filename);
  }

  retry(doc: DocumentItem): void {
    this.api.reprocess(doc.id).subscribe(() => {
      this.toast.success('Indexing started again.');
      this.reload();
    });
  }

  inspectAsk(question?: string): void {
    if (this.inspecting) this.ask(this.inspecting, question);
  }

  inspectRetry(): void {
    if (this.inspecting) this.retry(this.inspecting);
  }

  inspectDownload(): void {
    if (this.inspecting) this.download(this.inspecting);
  }

  inspectBrief(): string {
    return this.inspecting ? documentBrief(this.inspecting) : '';
  }

  inspectQuestions(): string[] {
    return this.inspecting ? starterQuestions(this.inspecting) : [];
  }
}
