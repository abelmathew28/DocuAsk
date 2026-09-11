import { Component, EventEmitter, Input, Output } from '@angular/core';
import { NgFor } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SampleDemo } from '../sample-docs';

@Component({
  selector: 'app-landing-demo-qa',
  imports: [NgFor, RouterLink],
  template: `
    <section id="product" class="marketing-section scroll-mt-20 py-6 sm:py-8" aria-labelledby="demo-heading">
      <div class="marketing-panel overflow-hidden">
        <div class="border-b border-paper-200 px-5 py-4 sm:px-6 dark:border-white/10">
          <div class="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p class="eyebrow">Interactive sample</p>
              <h2 id="demo-heading" class="mt-1 font-display text-2xl tracking-tight sm:text-3xl">Ask a sample question</h2>
            </div>
            <div class="flex flex-wrap gap-2" role="tablist" aria-label="Sample questions">
              <button
                *ngFor="let item of demos; let i = index"
                type="button"
                role="tab"
                class="chip"
                [class.is-on]="activeIndex === i"
                [attr.aria-selected]="activeIndex === i"
                (click)="select(i)"
              >
                {{ item.short }}
              </button>
            </div>
          </div>
        </div>
        <div class="grid gap-0 lg:grid-cols-[1.15fr_0.85fr]">
          <div class="space-y-4 px-5 py-5 sm:px-6">
            <div>
              <p class="text-[11px] uppercase tracking-[0.14em] text-ink-600">Question</p>
              <p class="mt-1 font-display text-xl leading-snug sm:text-2xl">{{ active.question }}</p>
            </div>
            <div>
              <p class="text-[11px] uppercase tracking-[0.14em] text-ink-600">Answer</p>
              <p class="mt-1 text-[15px] leading-7 text-ink-700">{{ active.answer }}</p>
            </div>
            <div class="border-t border-paper-200 pt-3 dark:border-white/10">
              <p class="text-[11px] uppercase tracking-[0.14em] text-ink-600">Citation</p>
              <p class="mt-1 text-sm font-medium text-accent-700">{{ active.citation }}</p>
              <p class="mt-1 text-xs text-ink-600">{{ active.section }} · Support: {{ active.supportStatus }}</p>
              <p class="mt-1 text-sm leading-6 text-ink-600">
                <span class="citation-highlight px-0.5">“{{ active.excerpt }}”</span>
              </p>
              <div class="mt-4 flex flex-wrap gap-2">
                <a routerLink="/demo" class="btn-ink">Open Source</a>
                <button type="button" class="btn-ghost" (click)="openPreview.emit()">View page preview</button>
              </div>
            </div>
          </div>
          <aside class="border-t border-paper-200 bg-white/70 px-5 py-5 sm:px-6 lg:border-l lg:border-t-0 dark:border-white/10 dark:bg-ink-950/40">
            <p class="text-[11px] uppercase tracking-[0.14em] text-ink-600">Source file</p>
            <p class="mt-1 font-medium">{{ active.file }}</p>
            <p class="mt-0.5 text-sm text-ink-600">Page {{ active.page }} · excerpt from indexed text</p>
            <div class="mt-4 rounded-md border border-paper-200 bg-paper-50 p-3 text-sm leading-6 text-ink-700 dark:border-white/10 dark:bg-ink-900">
              <p class="text-[11px] uppercase tracking-[0.14em] text-ink-600">Passage</p>
              <p class="mt-1">…{{ active.excerpt }}…</p>
            </div>
          </aside>
        </div>
      </div>
    </section>
  `,
})
export class LandingDemoQaComponent {
  @Input({ required: true }) demos: SampleDemo[] = [];
  @Input() activeIndex = 0;
  @Output() activeIndexChange = new EventEmitter<number>();
  @Output() openPreview = new EventEmitter<void>();

  get active(): SampleDemo {
    return this.demos[this.activeIndex] ?? this.demos[0];
  }

  select(index: number): void {
    this.activeIndexChange.emit(index);
  }
}
