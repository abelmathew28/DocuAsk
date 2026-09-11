import { Component } from '@angular/core';
import { NgFor } from '@angular/common';
import { RouterLink } from '@angular/router';
import { SiteHeaderComponent } from '../../shared/components/site-header.component';
import { SiteFooterComponent } from '../../shared/components/site-footer.component';

@Component({
  selector: 'app-use-cases',
  imports: [NgFor, RouterLink, SiteHeaderComponent, SiteFooterComponent],
  template: `
    <div class="min-h-screen bg-paper-50">
      <app-site-header></app-site-header>
      <article class="mx-auto max-w-3xl px-6 py-16">
        <h1 class="font-display text-5xl leading-[1.08] tracking-tight">Where it earns its keep</h1>
        <p class="mt-5 max-w-xl text-[15px] leading-7 text-ink-600">
          Upload your documents and find answers, compare information, extract data, and research across multiple files — then open the page that supports the answer.
        </p>
        <section *ngFor="let item of items" class="mt-12 border-t border-paper-200 pt-8">
          <h2 class="font-display text-2xl">{{ item.title }}</h2>
          <p class="mt-3 text-sm leading-7 text-ink-600">{{ item.body }}</p>
          <p class="mt-5 text-xs uppercase tracking-[0.14em] text-ink-600">Try asking</p>
          <ul class="mt-2 space-y-1 text-sm">
            <li *ngFor="let q of item.questions">“{{ q }}”</li>
          </ul>
        </section>
        <div class="mt-14 flex flex-wrap gap-3">
          <a routerLink="/demo" class="btn-ink">Try Live Demo</a>
          <a routerLink="/case-study" class="btn-ghost">Read the case study</a>
          <a routerLink="/register" class="btn-ghost">Create an account</a>
        </div>
      </article>
      <app-site-footer></app-site-footer>
    </div>
  `,
})
export class UseCasesComponent {
  items = [
    {
      title: 'Human resources',
      body: 'Handbooks are long because they have to be. People still need a fast answer on leave, hours, and reporting absences — then a page they can forward to a manager.',
      questions: ['What is the vacation policy?', 'How should employees report an absence?'],
    },
    {
      title: 'Operations',
      body: 'SOPs fail in the moment if nobody can find the clause. Keep the procedure in the PDF, and retrieve the step with a citation instead of paraphrasing from memory.',
      questions: ['What is the first step in this procedure?', 'Who must be notified?'],
    },
    {
      title: 'Legal and compliance reading',
      body: 'Not a substitute for counsel. A way to locate the sentence that actually says the thing, so the conversation starts on the right page.',
      questions: ['What limits are stated in this section?', 'What exceptions are listed?'],
    },
    {
      title: 'Research notes',
      body: 'Ask a paper or report what it claims. If the excerpt is thin, the product should refuse to decorate it.',
      questions: ['What result is reported?', 'What limitations does the author mention?'],
    },
  ];
}
