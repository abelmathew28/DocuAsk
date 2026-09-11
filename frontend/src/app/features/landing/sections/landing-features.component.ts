import { Component } from '@angular/core';
import { NgFor } from '@angular/common';
import { PRODUCT_FEATURES } from '../sample-docs';

@Component({
  selector: 'app-landing-features',
  imports: [NgFor],
  template: `
    <section class="marketing-section py-6 sm:py-8" aria-labelledby="features-heading">
      <div class="mb-4 max-w-2xl">
        <p class="eyebrow">Modes</p>
        <h2 id="features-heading" class="mt-2 font-display text-2xl tracking-tight sm:text-3xl">
          Ask, research, compare, extract
        </h2>
        <p class="mt-2 text-sm leading-6 text-ink-600">
          Four intents in one workspace — each returns evidence you can open in the file.
        </p>
      </div>
      <div class="grid gap-3 sm:grid-cols-2">
        <article *ngFor="let feature of features" class="marketing-panel p-5">
          <h3 class="font-display text-xl tracking-tight">{{ feature.title }}</h3>
          <p class="mt-2 text-sm leading-6 text-ink-600">{{ feature.body }}</p>
        </article>
      </div>
    </section>
  `,
})
export class LandingFeaturesComponent {
  readonly features = PRODUCT_FEATURES;
}
