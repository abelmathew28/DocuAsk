import { Component, ElementRef, HostListener, inject, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  LucideCopy,
  LucidePlus,
  LucideRefreshCw,
  LucideSend,
  LucideThumbsDown,
  LucideThumbsUp,
  LucideX,
} from '@lucide/angular';
import { ChatMessage, Conversation, DocumentItem, SearchScope, SourceCitation, AskMode } from '../../core/models/models';
import { ConversationService } from '../../core/services/conversation.service';
import { DocumentService } from '../../core/services/document.service';
import { IntelligenceService } from '../../core/services/intelligence.service';
import { MarkdownComponent } from '../../shared/components/markdown.component';
import { ConfirmDialogComponent } from '../../shared/components/confirm-dialog.component';
import { EmptyStateComponent } from '../../shared/components/empty-state.component';
import { DropzoneComponent } from '../../shared/components/dropzone.component';
import { SupportBadgeComponent } from '../../shared/components/support-badge.component';
import { PdfViewerComponent } from '../viewer/pdf-viewer.component';
import { ToastService } from '../../core/services/toast.service';
import { AuthService } from '../../core/services/auth.service';
import { documentBrief, starterQuestions } from '../../shared/document-starters';

@Component({
  selector: 'app-chat',
  imports: [
    NgIf,
    NgFor,
    FormsModule,
    RouterLink,
    MarkdownComponent,
    ConfirmDialogComponent,
    EmptyStateComponent,
    DropzoneComponent,
    SupportBadgeComponent,
    PdfViewerComponent,
    LucideCopy,
    LucideRefreshCw,
    LucideSend,
    LucideThumbsDown,
    LucideThumbsUp,
    LucidePlus,
    LucideX,
  ],
  templateUrl: './chat.component.html',
  host: {
    class: 'flex min-h-0 flex-1 flex-col overflow-hidden',
  },
})
export class ChatComponent implements OnInit, OnDestroy {
  private readonly conversationsApi = inject(ConversationService);
  private readonly documentsApi = inject(DocumentService);
  private readonly intelligence = inject(IntelligenceService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);
  readonly auth = inject(AuthService);

  documents: DocumentItem[] = [];
  conversations: Conversation[] = [];
  selectedDocumentId = '';
  checkedIds: string[] = [];
  scope: SearchScope = 'document';
  mode: AskMode = 'ask';
  compareA = '';
  compareB = '';
  conversationId = '';
  title = 'New conversation';
  messages: ChatMessage[] = [];
  draft = '';
  sending = false;
  askStage = 'Searching relevant sections…';
  loading = true;
  viewerOpen = false;
  viewerPage = 1;
  viewerDocId = '';
  viewerExcerpt = '';
  pendingDeleteId = '';
  renameOpen = false;
  renameValue = '';
  uploading = false;
  activeEvidence: ChatMessage | null = null;
  followUps: string[] = [];
  private poll?: ReturnType<typeof setInterval>;

  @ViewChild('thread') thread?: ElementRef<HTMLElement>;
  @ViewChild('composer') composer?: ElementRef<HTMLTextAreaElement>;

  ngOnInit(): void {
    this.refreshDocuments(() => {
      this.route.data.subscribe((data) => {
        const mode = data['mode'];
        if (mode === 'ask' || mode === 'research' || mode === 'compare' || mode === 'extract') {
          this.mode = mode;
          if (mode === 'research' && this.scope === 'document') this.scope = 'library';
        }
      });
      this.route.queryParamMap.subscribe((query) => {
        const qScope = query.get('scope');
        if (qScope === 'document' || qScope === 'selected' || qScope === 'library') {
          this.scope = qScope;
        }
        const qMode = query.get('mode');
        if (qMode === 'ask' || qMode === 'research' || qMode === 'compare' || qMode === 'extract') {
          this.setMode(qMode, false);
        }
        if (query.get('demo') === '1') {
          const calendar = this.documents.find((item) => item.status === 'ready' && /calendar|handbook|fall.?2026/i.test(item.name));
          if (calendar) this.selectedDocumentId = calendar.id;
        }
      });
      this.route.paramMap.subscribe((params) => {
        const id = params.get('id');
        if (id) {
          this.loadConversation(id);
          return;
        }
        const ready = this.preferredReady();
        if (ready && !this.selectedDocumentId) {
          this.selectedDocumentId = ready.id;
        }
        this.refreshConversations();
      });
    });
    this.poll = setInterval(() => {
      if (this.documents.some((doc) => doc.status === 'processing' || doc.status === 'uploading')) {
        this.refreshDocuments();
      }
    }, 3000);
  }

  ngOnDestroy(): void {
    if (this.poll) clearInterval(this.poll);
  }

  refreshDocuments(done?: () => void): void {
    this.documentsApi.list().subscribe((docs) => {
      this.documents = docs;
      this.loading = false;
      if (!this.selectedDocumentId) {
        const ready = this.preferredReady();
        if (ready) this.selectedDocumentId = ready.id;
      }
      done?.();
    });
  }

  upload(file: File): void {
    this.uploading = true;
    this.documentsApi.upload(file).subscribe({
      next: (doc) => {
        this.uploading = false;
        this.toast.success('Reading the document.');
        this.documents = [doc, ...this.documents.filter((item) => item.id !== doc.id)];
        this.selectedDocumentId = doc.id;
        if (this.scope === 'selected' && !this.checkedIds.includes(doc.id)) {
          this.checkedIds = [...this.checkedIds, doc.id];
        }
      },
      error: () => (this.uploading = false),
    });
  }

  readyDocuments(): DocumentItem[] {
    return this.documents.filter((item) => item.status === 'ready');
  }

  preferredReady(): DocumentItem | undefined {
    return (
      this.readyDocuments().find((item) => /calendar|fall.?2026|handbook/i.test(item.name)) ||
      this.readyDocuments()[0]
    );
  }

  setMode(mode: AskMode | string, navigate = true): void {
    if (mode !== 'ask' && mode !== 'research' && mode !== 'compare' && mode !== 'extract') return;
    this.mode = mode;
    if (mode === 'compare') {
      const ready = this.readyDocuments();
      if (!this.compareA && ready[0]) this.compareA = ready[0].id;
      if (!this.compareB && ready[1]) this.compareB = ready[1].id;
    }
    if (mode === 'research' && this.scope === 'document') {
      this.scope = 'library';
    }
    if (navigate) {
      const path = mode === 'ask' ? '/app/ask' : `/app/${mode}`;
      void this.router.navigate([path], { queryParamsHandling: 'preserve' });
    }
  }

  emptyTitle(): string {
    if (this.mode === 'research') return this.scope === 'library' ? 'Research the library' : 'Research these files';
    if (this.mode === 'compare') return 'Compare two documents';
    if (this.mode === 'extract') return 'Extract from these files';
    if (this.scope === 'library') return 'Your library';
    if (this.scope === 'selected') return this.checkedIds.length ? `${this.checkedIds.length} files` : 'Selected files';
    return this.selectedDocument()?.name || 'Ask this file';
  }

  documentBrief(): string {
    if (this.mode !== 'ask' || this.scope !== 'document') {
      if (this.mode === 'compare') return this.compareA && this.compareB ? '' : 'Choose two ready files.';
      return '';
    }
    return documentBrief(this.selectedDocument());
  }

  starterQuestions(): string[] {
    if (this.mode === 'extract') {
      return [
        'Extract dates and deadlines',
        'Extract requirements',
        'Extract contact information',
      ];
    }
    if (this.mode === 'compare') return [];
    if (this.scope === 'document') return starterQuestions(this.selectedDocument());
    if (this.scope === 'selected') {
      const first = this.documents.find((item) => this.checkedIds.includes(item.id));
      return starterQuestions(first);
    }
    return [];
  }

  composerPlaceholder(): string {
    if (!this.canAsk()) return 'Index a document before asking';
    if (this.mode === 'research') return 'Compare requirements, find conflicts, list dates…';
    if (this.mode === 'compare') return 'What changed between these files?';
    if (this.mode === 'extract') return 'Extract deadlines, contacts, requirements…';
    return 'Ask a question…';
  }

  setScope(scope: SearchScope): void {
    this.scope = scope;
    this.conversationId = '';
    this.messages = [];
    this.title = 'New conversation';
    if (scope === 'selected' && !this.checkedIds.length && this.selectedDocumentId) {
      this.checkedIds = [this.selectedDocumentId];
    }
    void this.router.navigate(['/app/ask'], { queryParams: { scope } });
    this.refreshConversations();
  }

  selectDocument(id: string): void {
    this.selectedDocumentId = id;
    if (this.scope === 'selected') {
      this.toggleChecked(id);
      return;
    }
    this.scope = 'document';
    this.conversationId = '';
    this.messages = [];
    this.refreshConversations();
  }

  toggleChecked(id: string): void {
    if (this.checkedIds.includes(id)) {
      this.checkedIds = this.checkedIds.filter((item) => item !== id);
    } else {
      this.checkedIds = [...this.checkedIds, id];
    }
  }

  openConversation(id: string): void {
    if (!id) return;
    void this.router.navigate(['/app/ask', id]);
  }

  refreshConversations(): void {
    const documentId = this.scope === 'document' ? this.selectedDocumentId : undefined;
    this.conversationsApi.list(documentId, this.scope).subscribe((items) => (this.conversations = items));
  }

  loadConversation(id: string): void {
    this.conversationId = id;
    this.conversationsApi.get(id).subscribe((detail) => {
      this.title = detail.title;
      this.selectedDocumentId = detail.document_id;
      this.scope = detail.scope || 'document';
      this.checkedIds = detail.document_ids?.length ? detail.document_ids : [detail.document_id];
      this.messages = detail.messages;
      this.activeEvidence = [...detail.messages].reverse().find((m) => m.role === 'assistant') || null;
      this.followUps = this.activeEvidence ? this.buildFollowUps(this.activeEvidence, '') : [];
      this.refreshConversations();
      this.scrollToBottom();
      const pending = (history.state?.draft as string | undefined)?.trim();
      if (pending && !detail.messages.length) {
        history.replaceState({}, '');
        this.draft = pending;
        this.send();
      }
    });
  }

  createPayload() {
    if (this.scope === 'library') {
      return { scope: 'library' as const, title: 'Library search' };
    }
    if (this.scope === 'selected') {
      const ids = this.checkedIds.length ? this.checkedIds : this.selectedDocumentId ? [this.selectedDocumentId] : [];
      return { scope: 'selected' as const, document_ids: ids, title: 'Selected files' };
    }
    return { scope: 'document' as const, document_id: this.selectedDocumentId };
  }

  newConversation(): void {
    if (!this.canAsk()) return;
    this.conversationsApi.create(this.createPayload()).subscribe((conversation) => {
      void this.router.navigate(['/app/ask', conversation.id]);
    });
  }

  send(): void {
    const content = this.draft.trim();
    if (!content || this.sending || !this.canAsk()) return;
    if (!this.conversationId) {
      this.sending = true;
      this.conversationsApi.create(this.createPayload()).subscribe({
        next: (conversation) => {
          this.conversationId = conversation.id;
          void this.router.navigate(['/app/ask', conversation.id]);
          this.submit(content);
        },
        error: () => (this.sending = false),
      });
      return;
    }
    this.submit(content);
  }

  private submit(content: string): void {
    this.draft = '';
    this.sending = true;
    this.askStage = this.mode === 'compare' ? 'Comparing sources…' : 'Searching relevant sections…';
    this.messages = [
      ...this.messages,
      { id: 'temp-user', role: 'user', content, feedback: null, created_at: new Date().toISOString(), sources: [] },
    ];
    this.scrollToBottom();
    window.setTimeout(() => {
      if (this.sending) this.askStage = 'Checking sources…';
    }, 600);
    window.setTimeout(() => {
      if (this.sending) this.askStage = 'Generating response…';
    }, 1400);

    const handle = {
      next: (res: { user_message: ChatMessage; assistant_message: ChatMessage }) => {
        this.messages = this.messages.filter((item) => item.id !== 'temp-user');
        this.messages = [...this.messages, res.user_message, res.assistant_message];
        this.activeEvidence = res.assistant_message;
        this.followUps = this.buildFollowUps(res.assistant_message, content);
        this.sending = false;
        this.title =
          this.title === 'New conversation' || this.title === 'Library search' || this.title === 'Selected files'
            ? content.slice(0, 48)
            : this.title;
        this.refreshConversations();
        this.scrollToBottom();
      },
      error: () => {
        this.sending = false;
      },
    };

    if (this.mode === 'compare') {
      if (!this.compareA || !this.compareB || this.compareA === this.compareB) {
        this.sending = false;
        this.messages = this.messages.filter((item) => item.id !== 'temp-user');
        this.toast.success('Choose two different ready files to compare.');
        return;
      }
      this.intelligence
        .compare({
          document_a_id: this.compareA,
          document_b_id: this.compareB,
          question: content,
          conversation_id: this.conversationId || undefined,
        })
        .subscribe(handle);
      return;
    }

    const mode = this.mode === 'research' || this.mode === 'extract' ? this.mode : 'ask';
    this.conversationsApi.sendMessage(this.conversationId, content, mode).subscribe(handle);
  }

  regenerate(): void {
    if (!this.conversationId || this.sending) return;
    this.sending = true;
    this.conversationsApi.regenerate(this.conversationId).subscribe({
      next: (res) => {
        const withoutLastAssistant = [...this.messages];
        const lastAssistant = [...withoutLastAssistant].reverse().find((item) => item.role === 'assistant');
        this.messages = withoutLastAssistant.filter((item) => item.id !== lastAssistant?.id);
        this.messages = [...this.messages, res.assistant_message];
        this.sending = false;
        this.scrollToBottom();
      },
      error: () => (this.sending = false),
    });
  }

  copy(text: string): void {
    void navigator.clipboard.writeText(text);
    this.toast.success('Copied.');
  }

  copyAnswer(message: ChatMessage): void {
    const sources = message.sources
      .map((source) => `- ${source.document} — Page ${source.page}: ${source.excerpt}`)
      .join('\n');
    this.copy(sources ? `${message.content}\n\nSources\n${sources}` : message.content);
  }

  copyCitation(source: SourceCitation): void {
    this.copy(`${source.document} — Page ${source.page}`);
  }

  copyThread(): void {
    if (!this.messages.length) return;
    const body = this.messages
      .map((message) => {
        const sources = message.sources.map((source) => `  - ${source.document} — Page ${source.page}`).join('\n');
        return `## ${message.role}\n\n${message.content}${sources ? `\n\n${sources}` : ''}`;
      })
      .join('\n\n');
    this.copy(`# ${this.title}\n\n${body}`);
  }

  rate(message: ChatMessage, rating: 'up' | 'down'): void {
    this.conversationsApi.feedback(this.conversationId, message.id, rating).subscribe(() => {
      message.feedback = rating;
    });
  }

  openSource(source: SourceCitation): void {
    const doc = this.documents.find((item) => item.id === (source.document_id || this.selectedDocumentId));
    this.viewerDocId = source.document_id || this.selectedDocumentId;
    this.viewerPage = source.page;
    this.viewerExcerpt = source.excerpt;
    if (doc && doc.document_type && doc.document_type !== 'pdf') {
      this.toast.success(`${source.document} — page ${source.page}`);
    }
    this.viewerOpen = true;
  }

  saveRename(): void {
    if (!this.conversationId || !this.renameValue.trim()) return;
    this.conversationsApi.rename(this.conversationId, this.renameValue.trim()).subscribe((item) => {
      this.title = item.title;
      this.renameOpen = false;
      this.refreshConversations();
    });
  }

  deleteConversation(): void {
    if (!this.pendingDeleteId) return;
    this.conversationsApi.delete(this.pendingDeleteId).subscribe(() => {
      this.pendingDeleteId = '';
      void this.router.navigate(['/app/ask']);
      this.messages = [];
      this.conversationId = '';
      this.activeEvidence = null;
      this.refreshConversations();
    });
  }

  selectEvidence(message: ChatMessage): void {
    if (message.role === 'assistant') this.activeEvidence = message;
  }

  evidenceSources(): SourceCitation[] {
    return this.activeEvidence?.sources || [];
  }

  selectedDocument(): DocumentItem | undefined {
    return this.documents.find((item) => item.id === this.selectedDocumentId);
  }

  scopeLabel(): string {
    if (this.scope === 'library') return 'Entire library';
    if (this.scope === 'selected') {
      const count = this.checkedIds.length || 1;
      return `${count} selected file${count === 1 ? '' : 's'}`;
    }
    return this.selectedDocument()?.name || 'Select a document';
  }

  canAsk(): boolean {
    if (this.mode === 'compare') {
      return this.readyDocuments().length >= 2;
    }
    if (this.scope === 'library') return this.readyDocuments().length > 0;
    if (this.scope === 'selected') return this.checkedIds.some((id) => this.documents.find((doc) => doc.id === id)?.status === 'ready');
    return this.selectedDocument()?.status === 'ready';
  }

  composerDisabled(): boolean {
    return this.sending || !this.canAsk();
  }

  isInsufficient(message: ChatMessage): boolean {
    if (message.role !== 'assistant') return false;
    if (message.sources.length) return false;
    return /couldn't find enough information|could not find enough information/i.test(message.content);
  }

  useSuggestion(question: string): void {
    this.draft = question;
    this.followUps = [];
    this.send();
  }

  buildFollowUps(message: ChatMessage, question: string): string[] {
    if (this.isInsufficient(message)) {
      return ['Try a more specific question from this file', 'Search the entire library instead'];
    }
    if (this.mode === 'extract') {
      return ['Extract deadlines and dates', 'Extract contact information', 'Export fields as CSV'];
    }
    if (this.mode === 'compare') {
      return ['Summarize the main differences', 'Which file is more restrictive?'];
    }
    if (this.mode === 'research') {
      return ['List supporting evidence only', 'Are there any conflicting statements?'];
    }
    const lower = question.toLowerCase();
    const ideas: string[] = [];
    if (/skill|experience|education/i.test(lower)) {
      ideas.push('What dates and employers are listed?', 'Summarize education and certifications');
    } else if (/withdraw|refund|deadline|policy/i.test(lower)) {
      ideas.push('What is the tuition refund schedule?', 'Are there exceptions to this policy?');
    } else {
      ideas.push('Show the exact source wording', 'What related deadlines are mentioned?');
    }
    if (message.sources.length) {
      ideas.push(`Open page ${message.sources[0].page} for more context`);
    }
    return ideas.slice(0, 3);
  }

  exportExtractCsv(): void {
    const ids =
      this.scope === 'library'
        ? this.readyDocuments().map((d) => d.id)
        : this.scope === 'selected'
          ? this.checkedIds
          : this.selectedDocumentId
            ? [this.selectedDocumentId]
            : [];
    if (!ids.length) {
      this.toast.success('Select at least one ready document to export.');
      return;
    }
    this.intelligence.exportExtractCsv(ids).subscribe({
      next: (csv) => {
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'docuask-extract.csv';
        a.click();
        URL.revokeObjectURL(url);
        this.toast.success('CSV downloaded.');
      },
      error: () => this.toast.error('Could not export CSV right now.'),
    });
  }

  exportThread(): void {
    if (!this.conversationId) return;
    this.conversationsApi.exportMarkdown(this.conversationId, this.title);
  }

  downloadDoc(): void {
    const doc = this.selectedDocument();
    if (!doc || this.scope !== 'document') return;
    this.documentsApi.download(doc.id, doc.original_filename);
  }

  onComposerKey(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }

  @HostListener('document:keydown', ['$event'])
  onPageKey(event: KeyboardEvent): void {
    if (event.key === '/' && !this.isTyping(event)) {
      event.preventDefault();
      this.composer?.nativeElement.focus();
    }
    if (event.key === 'Escape' && this.viewerOpen) {
      this.viewerOpen = false;
    }
  }

  private isTyping(event: KeyboardEvent): boolean {
    const target = event.target as HTMLElement | null;
    return !!target && ['INPUT', 'TEXTAREA'].includes(target.tagName);
  }

  private scrollToBottom(): void {
    queueMicrotask(() => {
      const el = this.thread?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }
}
