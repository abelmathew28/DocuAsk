import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-landing-cta',
  imports: [RouterLink],
  template: `
    <section class="marketing-section py-8 sm:py-12" aria-labelledby="cta-heading">
      <div class="marketing-panel hero-wash px-6 py-10 text-center sm:px-8 sm:py-10">
        <h2 id="cta-heading" class="font-display text-2xl tracking-tight sm:text-3xl sm:text-4xl">
          Try the live demo
        </h2>
        <p class="mx-auto mt-4 max-w-lg text-sm leading-6 text-ink-600">
          Open a seeded employee handbook, ask a question, and follow the citation to the page.
          No credit card — just a working document workspace.
        </p>
        <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
          <a routerLink="/demo" class="btn-ink">Try Live Demo</a>
          <a routerLink="/case-study" class="btn-ghost">Read the case study</a>
        </div>
      </div>
    </section>
  `,
})
export class LandingCtaComponent {}
