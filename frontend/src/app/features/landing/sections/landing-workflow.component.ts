import { Component } from '@angular/core';
import { NgFor } from '@angular/common';
import { WORKFLOW_STEPS } from '../sample-docs';

@Component({
  selector: 'app-landing-workflow',
  imports: [NgFor],
  template: `
    <section id="how" class="marketing-section scroll-mt-24 py-6 sm:py-8" aria-labelledby="workflow-heading">
      <div class="marketing-panel px-5 py-5 sm:px-6">
        <p class="eyebrow">How it works</p>
        <h2 id="workflow-heading" class="mt-2 font-display text-2xl tracking-tight sm:text-3xl">
          Upload → Extract → Search → Answer → Verify
        </h2>
        <p class="mt-3 max-w-2xl text-sm leading-6 text-ink-600">
          A short pipeline from file to cited answer — designed so you can check the source, not trust a black box.
        </p>
        <ol class="mt-5 divide-y divide-paper-200 border-y border-paper-200 dark:divide-white/10 dark:border-white/10">
          <li *ngFor="let step of steps; let i = index" class="grid gap-1 py-3.5 sm:grid-cols-[4rem_1fr] sm:items-baseline">
            <span class="text-sm text-accent-600">{{ i + 1 }}</span>
            <div>
              <h3 class="font-medium">{{ step.title }}</h3>
              <p class="mt-0.5 text-sm leading-6 text-ink-600">{{ step.body }}</p>
            </div>
          </li>
        </ol>
      </div>
    </section>
  `,
})
export class LandingWorkflowComponent {
  readonly steps = WORKFLOW_STEPS;
}
