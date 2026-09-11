import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-landing-hero',
  imports: [RouterLink],
  template: `
    <section class="marketing-section pb-6 pt-12 sm:pb-8 sm:pt-16" aria-labelledby="hero-heading">
      <div class="grid items-end gap-8 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <div>
          <p class="eyebrow text-accent-600">Document-grounded Q&amp;A</p>
          <h1 id="hero-heading" class="mt-3 font-display text-4xl leading-[1.08] tracking-tight text-ink-950 sm:text-5xl lg:text-[3.25rem]">
            Ask your documents. Verify every answer.
          </h1>
          <p class="mt-4 max-w-xl text-[15px] leading-7 text-ink-600">
            DocuAsk searches your trusted documents, generates grounded answers, and shows the exact evidence behind every response.
          </p>
          <div class="mt-6 flex flex-wrap items-center gap-3">
            <a routerLink="/demo" class="btn-ink">Try the Interactive Demo</a>
            <a routerLink="/case-study" class="btn-ghost">View Case Study</a>
          </div>
        </div>
        <aside class="marketing-panel hidden p-5 sm:block" aria-hidden="true">
          <p class="text-[11px] uppercase tracking-[0.14em] text-ink-600">Sample citation</p>
          <p class="mt-3 font-medium">Fall-2026-Academic-Calendar.pdf — Page 2</p>
          <p class="mt-2 text-sm leading-6 text-ink-600">
            <span class="citation-highlight px-0.5">“Last day to withdraw from a Fall 2026 course: Friday, November 6, 2026.”</span>
          </p>
          <p class="mt-4 text-xs text-ink-600">Nodes in the background = documents, pages, and passages.</p>
        </aside>
      </div>
    </section>
  `,
})
export class LandingHeroComponent {}
