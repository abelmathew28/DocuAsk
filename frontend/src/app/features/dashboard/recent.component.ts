import { Component, inject, OnInit, signal } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ConversationService } from '../../core/services/conversation.service';
import { Conversation } from '../../core/models/models';
import { EmptyStateComponent } from '../../shared/components/empty-state.component';
import { relativeTime } from '../../shared/utils';

@Component({
  selector: 'app-recent',
  imports: [NgIf, NgFor, RouterLink, EmptyStateComponent],
  template: `
    <h1 class="font-display text-4xl tracking-tight">Activity</h1>
    <p class="mt-2 max-w-xl text-sm leading-6 text-ink-600">Threads across this account. Open one to continue, export, or check the last citation.</p>
    <app-empty-state *ngIf="!items().length" class="mt-6" title="No conversations yet" message="Open a ready document and ask a question you can verify on a page."></app-empty-state>
    <ul class="mt-8">
      <li *ngFor="let item of items()">
        <a [routerLink]="['/app/ask', item.id]" class="block border-b border-paper-200 py-4 dark:border-white/10">
          <p class="font-medium">{{ item.title }}</p>
          <p class="mt-1 text-xs text-ink-600">{{ item.scope === 'library' ? 'Entire library' : item.scope === 'selected' ? 'Selected files' : item.document_name }} · {{ relativeTime(item.updated_at) }}</p>
          <p *ngIf="item.preview" class="mt-2 line-clamp-2 text-sm leading-6 text-ink-600">{{ item.preview }}</p>
        </a>
      </li>
    </ul>
  `,
})
export class RecentComponent implements OnInit {
  private readonly api = inject(ConversationService);
  items = signal<Conversation[]>([]);
  relativeTime = relativeTime;

  ngOnInit(): void {
    this.api.list().subscribe((items) => this.items.set(items));
  }
}
