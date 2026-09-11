import { Component, Input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SampleDemo } from '../sample-docs';

@Component({
  selector: 'app-landing-citation-preview',
  imports: [RouterLink],
  template: `
    <section id="citation" class="marketing-section scroll-mt-24 py-6 sm:py-8" aria-labelledby="citation-heading">
      <div class="grid items-start gap-8 lg:grid-cols-[1fr_1.05fr]">
        <div>
          <p class="eyebrow">Citations</p>
          <h2 id="citation-heading" class="mt-2 font-display text-2xl tracking-tight sm:text-3xl">
            Every answer points back to a page
          </h2>
          <p class="mt-3 max-w-md text-sm leading-6 text-ink-600">
            DocuAsk shows the document name, page number, and excerpt so you can verify the claim in context —
            not a chat reply floating free of the source.
          </p>
          <a routerLink="/demo" class="btn-ink mt-6">Try with the demo handbook</a>
        </div>
        <div class="marketing-panel page-preview overflow-hidden">
          <div class="flex items-center justify-between border-b border-paper-200 px-4 py-3 text-xs text-ink-600 dark:border-white/10">
            <span>{{ demo.file }}</span>
            <span>Page {{ demo.page }}</span>
          </div>
          <div class="space-y-3 px-5 py-6 text-sm leading-7 text-ink-700">
            <p class="text-ink-400">…prior section continues above…</p>
            <p>
              Eligible full-time staff accrue leave monthly.
              <mark class="citation-highlight rounded-sm px-0.5 text-ink-950">{{ demo.excerpt }}</mark>
              Unused days follow the policy in this handbook.
            </p>
            <p class="text-ink-400">…following paragraphs continue below…</p>
          </div>
          <div class="border-t border-paper-200 px-4 py-3 text-sm dark:border-white/10">
            <a routerLink="/demo" class="font-medium text-accent-700 hover:underline">Open source in live demo →</a>
          </div>
        </div>
      </div>
    </section>
  `,
})
export class LandingCitationPreviewComponent {
  @Input({ required: true }) demo!: SampleDemo;
}
