import { Component } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { ARCHITECTURE_NODES } from '../sample-docs';

@Component({
  selector: 'app-landing-architecture',
  imports: [NgFor, NgIf],
  template: `
    <section class="marketing-section py-6 sm:py-8" aria-labelledby="arch-heading">
      <div class="marketing-panel px-5 py-5 sm:px-6">
        <p class="eyebrow">Architecture</p>
        <h2 id="arch-heading" class="mt-2 font-display text-2xl tracking-tight sm:text-3xl">
          Built as a RAG workspace
        </h2>
        <p class="mt-3 max-w-2xl text-sm leading-6 text-ink-600">
          Angular client, FastAPI API, embeddings and vector retrieval, page-aware processing, authentication, and storage —
          answers come from retrieved passages, then citations point you back.
        </p>
        <ol class="mt-8 flex flex-wrap items-center gap-2 text-sm">
          <ng-container *ngFor="let node of nodes; let last = last">
            <li class="rounded-md border border-paper-200 bg-white px-3 py-2 font-medium dark:border-white/10 dark:bg-ink-900">
              {{ node }}
            </li>
            <li *ngIf="!last" class="text-ink-400" aria-hidden="true">→</li>
          </ng-container>
        </ol>
      </div>
    </section>
  `,
})
export class LandingArchitectureComponent {
  readonly nodes = ARCHITECTURE_NODES;
}
