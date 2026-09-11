import { Component } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SiteHeaderComponent } from '../../shared/components/site-header.component';
import { SiteFooterComponent } from '../../shared/components/site-footer.component';
import { KnowledgeNetworkCanvasComponent } from './knowledge-network-canvas.component';
import { ARCHITECTURE_NODES } from './sample-docs';

@Component({
  selector: 'app-architecture',
  imports: [NgFor, NgIf, RouterLink, SiteHeaderComponent, SiteFooterComponent, KnowledgeNetworkCanvasComponent],
  template: `
    <a class="skip-link" href="#arch-main">Skip to content</a>
    <div class="relative min-h-screen overflow-x-hidden bg-paper-50 text-ink-950">
      <app-knowledge-network-canvas [intensity]="0.55"></app-knowledge-network-canvas>
      <app-site-header></app-site-header>
      <article id="arch-main" class="marketing-section py-10 sm:py-12">
        <header class="marketing-panel max-w-3xl px-5 py-6 sm:px-8">
          <p class="eyebrow text-accent-600">Architecture</p>
          <h1 class="mt-2 font-display text-3xl tracking-tight sm:text-4xl">
            Angular → FastAPI → Retrieval → Verified answers
          </h1>
          <p class="mt-3 text-[15px] leading-7 text-ink-600">
            DocuAsk is an application layer around retrieval and citation — not a foundation-model training project.
            Every answer is constrained to passages retrieved from the user’s documents.
          </p>
        </header>

        <section class="marketing-panel mt-4 max-w-3xl px-5 py-5 sm:px-8" aria-labelledby="pipeline">
          <h2 id="pipeline" class="font-display text-2xl tracking-tight">Pipeline</h2>
          <ol class="mt-4 flex flex-wrap items-center gap-2 text-sm">
            <ng-container *ngFor="let node of nodes; let last = last">
              <li class="rounded-md border border-paper-200 bg-white px-3 py-2 font-medium dark:border-white/10 dark:bg-ink-900">
                {{ node }}
              </li>
              <li *ngIf="!last" class="text-ink-400" aria-hidden="true">→</li>
            </ng-container>
          </ol>
          <ul class="mt-5 list-disc space-y-2 pl-5 text-[15px] leading-7 text-ink-700">
            <li>Upload PDF, DOCX, or TXT; extract text (OCR fallback for scanned PDFs).</li>
            <li>Chunk by structure; embed with a swappable provider (local or OpenAI).</li>
            <li>Hybrid keyword + vector search, then lexical or cross-encoder rerank.</li>
            <li>Grounded answer generation with extractive fallback when the LLM is unavailable.</li>
            <li>Citation verification against retrieved passages; abstain when evidence is missing.</li>
          </ul>
        </section>

        <section class="marketing-panel mt-4 max-w-3xl px-5 py-5 sm:px-8" aria-labelledby="stack">
          <h2 id="stack" class="font-display text-2xl tracking-tight">Stack</h2>
          <dl class="mt-4 divide-y divide-paper-200 border-y border-paper-200 text-sm dark:divide-white/10 dark:border-white/10">
            <div class="grid gap-1 py-3 sm:grid-cols-[9rem_1fr]">
              <dt class="font-medium">Frontend</dt>
              <dd class="text-ink-700">Angular 19, Tailwind, PDF.js viewer</dd>
            </div>
            <div class="grid gap-1 py-3 sm:grid-cols-[9rem_1fr]">
              <dt class="font-medium">Backend</dt>
              <dd class="text-ink-700">FastAPI, SQLAlchemy, JWT auth, Argon2 passwords</dd>
            </div>
            <div class="grid gap-1 py-3 sm:grid-cols-[9rem_1fr]">
              <dt class="font-medium">API</dt>
              <dd class="text-ink-700">Versioned modules under <code class="text-xs">/api</code> (configurable prefix)</dd>
            </div>
            <div class="grid gap-1 py-3 sm:grid-cols-[9rem_1fr]">
              <dt class="font-medium">Storage</dt>
              <dd class="text-ink-700">Per-user paths on disk or S3-compatible object storage</dd>
            </div>
          </dl>
          <div class="mt-6 flex flex-wrap gap-2">
            <a routerLink="/case-study" class="btn-ink">Case study</a>
            <a routerLink="/demo" class="btn-ghost">Try live demo</a>
          </div>
        </section>
      </article>
      <app-site-footer></app-site-footer>
    </div>
  `,
})
export class ArchitectureComponent {
  readonly nodes = ARCHITECTURE_NODES;
}
