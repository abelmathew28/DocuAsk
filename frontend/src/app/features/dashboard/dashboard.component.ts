import { Component, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { DecimalPipe, NgFor, NgIf } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { DocumentService } from '../../core/services/document.service';
import { ConversationService } from '../../core/services/conversation.service';
import { UserService } from '../../core/services/user.service';
import { Conversation, DashboardStats, DocumentItem } from '../../core/models/models';
import { DropzoneComponent } from '../../shared/components/dropzone.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge.component';
import { ToastService } from '../../core/services/toast.service';
import { relativeTime, explainDocumentError } from '../../shared/utils';
import { starterQuestions } from '../../shared/document-starters';

@Component({
  selector: 'app-dashboard',
  imports: [NgIf, NgFor, DecimalPipe, RouterLink, DropzoneComponent, StatusBadgeComponent],
  templateUrl: './dashboard.component.html',
})
export class DashboardComponent implements OnInit, OnDestroy {
  private readonly documentsApi = inject(DocumentService);
  private readonly conversationsApi = inject(ConversationService);
  private readonly users = inject(UserService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  private poll?: ReturnType<typeof setInterval>;

  documents = signal<DocumentItem[]>([]);
  conversations = signal<Conversation[]>([]);
  stats = signal<DashboardStats | null>(null);
  loading = true;
  relativeTime = relativeTime;
  explainError = explainDocumentError;

  get readyDoc(): DocumentItem | undefined {
    const ready = this.documents().filter((item) => item.status === 'ready');
    return ready.find((item) => /calendar|fall.?2026|handbook/i.test(item.name)) || ready[0];
  }

  get processingCount(): number {
    return this.documents().filter((item) => item.status === 'processing' || item.status === 'uploading').length;
  }

  processingLabel(): string {
    const item = this.documents().find((doc) => doc.status === 'processing' || doc.status === 'uploading');
    const stage = item?.processing_stage;
    if (stage === 'reading') return 'reading';
    if (stage === 'understanding') return 'understanding structure';
    if (stage === 'indexing') return 'preparing search';
    return 'indexing';
  }

  ngOnInit(): void {
    this.refresh();
    this.users.stats().subscribe({
      next: (value) => this.stats.set(value),
      error: () => this.stats.set(null),
    });
    this.poll = setInterval(() => {
      if (this.processingCount) this.refresh();
    }, 3000);
  }

  ngOnDestroy(): void {
    if (this.poll) clearInterval(this.poll);
  }

  refresh(): void {
    this.documentsApi.list().subscribe((items) => {
      this.documents.set(items);
      this.loading = false;
    });
    this.conversationsApi.list().subscribe((items) => this.conversations.set(items.slice(0, 6)));
  }

  upload(file: File): void {
    this.documentsApi.upload(file).subscribe({
      next: (doc) => {
        this.toast.success('Reading the document.');
        this.documents.update((items) => [doc, ...items]);
      },
    });
  }

  retry(doc: DocumentItem): void {
    this.documentsApi.reprocess(doc.id).subscribe((updated) => {
      this.documents.update((items) => items.map((item) => (item.id === updated.id ? updated : item)));
    });
  }

  openChat(doc: DocumentItem, question?: string): void {
    this.conversationsApi.create({ document_id: doc.id, title: question?.slice(0, 48) }).subscribe((conversation) => {
      void this.router.navigate(['/app/ask', conversation.id], question ? { state: { draft: question } } : undefined);
    });
  }

  askReady(question: string): void {
    const doc = this.readyDoc;
    if (doc) this.openChat(doc, question);
  }

  readyQuestions(): string[] {
    return starterQuestions(this.readyDoc);
  }
}
