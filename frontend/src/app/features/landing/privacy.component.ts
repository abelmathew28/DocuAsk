import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SiteHeaderComponent } from '../../shared/components/site-header.component';
import { SiteFooterComponent } from '../../shared/components/site-footer.component';

@Component({
  selector: 'app-privacy',
  imports: [RouterLink, SiteHeaderComponent, SiteFooterComponent],
  template: `
    <div class="min-h-screen bg-paper-50">
      <app-site-header></app-site-header>
      <article class="mx-auto max-w-3xl px-6 py-16">
        <h1 class="font-display text-5xl">Privacy</h1>
        <p class="mt-6 text-[17px] leading-8 text-ink-700">
          DocuAsk stores account data, uploaded files, extracted text, embeddings, and conversation history so the product can answer from your documents.
          Passwords are hashed. API keys are not stored in the browser. You can delete documents, conversations, or the whole account from Settings.
        </p>
        <ul class="mt-8 space-y-3 text-sm leading-7 text-ink-600">
          <li>Account: name, email, hashed password, theme preference.</li>
          <li>Library: original PDF, extracted pages, embeddings, summary, suggested questions.</li>
          <li>Threads: questions, answers, citations, and optional feedback.</li>
        </ul>
        <a routerLink="/" class="mt-8 inline-block text-sm font-medium text-accent-600">Back to home →</a>
      </article>
      <app-site-footer></app-site-footer>
    </div>
  `,
})
export class PrivacyComponent {}
