import { Component, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { NgFor, NgIf } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { LogoComponent } from '../../shared/components/logo.component';
import { KnowledgeNetworkCanvasComponent } from '../landing/knowledge-network-canvas.component';
import { OFFLINE_DEMO_QA, SAMPLE_DEMOS } from '../landing/sample-docs';
import { apiError } from '../../shared/utils';

@Component({
  selector: 'app-demo-entry',
  imports: [NgIf, NgFor, RouterLink, LogoComponent, KnowledgeNetworkCanvasComponent],
  template: `
    <div class="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-paper-50 px-4 dark:bg-ink-950">
      <app-knowledge-network-canvas [highlightIds]="highlightIds" [intensity]="0.7"></app-knowledge-network-canvas>
      <div class="relative z-10 w-full max-w-lg text-center">
        <app-logo></app-logo>
        <ng-container *ngIf="!offline; else offlineBlock">
          <h1 class="mt-8 font-display text-3xl">Opening the demo</h1>
          <p class="mt-2 text-sm leading-6 text-ink-600">
            Signing you into a sample higher-education library. Ask about withdrawal deadlines, then open the cited page.
          </p>
          <p *ngIf="error" class="mt-4 text-sm text-red-600">{{ error }}</p>
          <p *ngIf="!error" class="processing-dot mt-6 text-sm text-ink-600">Preparing the workspace…</p>
        </ng-container>
        <ng-template #offlineBlock>
          <p class="mt-8 inline-block rounded-md border border-accent-200 bg-accent-50 px-2 py-1 text-[11px] uppercase tracking-[0.14em] text-accent-700">
            Demo sample
          </p>
          <h1 class="mt-3 font-display text-3xl">Interactive demo (offline)</h1>
          <p class="mt-2 text-sm leading-6 text-ink-600">
            The API is unavailable, so these answers are seeded from public sample documents — not a live model call.
          </p>
          <div class="mt-6 flex flex-wrap justify-center gap-2">
            <button
              *ngFor="let item of samples; let i = index"
              type="button"
              class="chip"
              [class.is-on]="active === i"
              (click)="select(i)"
            >
              {{ item.short }}
            </button>
          </div>
          <div class="marketing-panel mt-6 p-5 text-left">
            <p class="text-[11px] uppercase tracking-[0.14em] text-ink-600">Question</p>
            <p class="mt-1 font-display text-xl leading-snug">{{ activeSample.question }}</p>
            <p class="mt-4 text-[11px] uppercase tracking-[0.14em] text-ink-600">Answer</p>
            <p class="mt-1 text-sm leading-6 text-ink-700">{{ activeSample.answer }}</p>
            <p class="mt-4 text-[11px] uppercase tracking-[0.14em] text-ink-600">Evidence</p>
            <p class="mt-1 text-sm font-medium text-accent-700">{{ activeSample.citation }}</p>
            <p class="mt-1 text-sm leading-6 text-ink-600">
              <span class="citation-highlight px-0.5">“{{ activeSample.excerpt }}”</span>
            </p>
            <p class="mt-3 text-xs text-ink-600">Support status: {{ activeSample.supportStatus }}</p>
          </div>
          <a routerLink="/" class="btn-ghost mt-6 inline-flex">Back to home</a>
        </ng-template>
      </div>
    </div>
  `,
})
export class DemoEntryComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  error = '';
  offline = false;
  active = 0;
  readonly samples = SAMPLE_DEMOS;
  readonly offlineQa = OFFLINE_DEMO_QA;

  get activeSample() {
    return this.samples[this.active] ?? this.samples[0];
  }

  get highlightIds(): number[] {
    return this.activeSample?.highlightIds ?? [];
  }

  constructor() {
    this.auth.demoLogin().subscribe({
      next: () => this.router.navigate(['/app/ask'], { queryParams: { demo: '1' } }),
      error: (err) => {
        this.error = apiError(err, 'The live demo is not available right now.');
        this.offline = true;
      },
    });
  }

  select(index: number): void {
    this.active = index;
  }
}
