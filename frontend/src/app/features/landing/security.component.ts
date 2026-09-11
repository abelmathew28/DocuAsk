import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SiteHeaderComponent } from '../../shared/components/site-header.component';
import { SiteFooterComponent } from '../../shared/components/site-footer.component';
import { KnowledgeNetworkCanvasComponent } from './knowledge-network-canvas.component';

@Component({
  selector: 'app-security',
  imports: [RouterLink, SiteHeaderComponent, SiteFooterComponent, KnowledgeNetworkCanvasComponent],
  template: `
    <a class="skip-link" href="#security-main">Skip to content</a>
    <div class="relative min-h-screen overflow-x-hidden bg-paper-50">
      <app-knowledge-network-canvas></app-knowledge-network-canvas>
      <app-site-header></app-site-header>
      <article id="security-main" class="marketing-section py-10 sm:py-12">
        <div class="marketing-panel max-w-3xl px-5 py-6 sm:px-8">
          <p class="eyebrow text-accent-600">Security</p>
          <h1 class="mt-2 font-display text-3xl tracking-tight sm:text-4xl">
            Private storage, scoped access, server-side keys
          </h1>
          <div class="mt-5 space-y-4 text-[15px] leading-7 text-ink-700">
            <p>
              DocuAsk is built so answers stay tied to <em>your</em> documents. Passwords are hashed with Argon2.
              Access tokens are short-lived JWTs; refresh tokens are stored hashed and can be revoked.
            </p>
            <p>
              Every document, chunk, conversation, and message is loaded with the current user id.
              Changing an identifier in the URL does not reveal another person’s file.
            </p>
            <p>
              Uploads are checked for type, size, and encryption. Storage can stay on disk in development
              or move to object storage in production without changing the product API.
            </p>
            <p>
              API keys never ship in the Angular bundle. The browser talks to DocuAsk; DocuAsk talks to the model.
              Uploaded content is used to answer your questions — not presented as training data for a public model by default.
            </p>
          </div>
          <dl class="mt-6 divide-y divide-paper-200 border-y border-paper-200 text-sm dark:divide-white/10 dark:border-white/10">
            <div class="grid gap-2 py-3 sm:grid-cols-[11rem_1fr]">
              <dt class="font-medium">Private storage</dt>
              <dd class="text-ink-600">Files and indexes owned by account.</dd>
            </div>
            <div class="grid gap-2 py-4 sm:grid-cols-[11rem_1fr]">
              <dt class="font-medium">Access controls</dt>
              <dd class="text-ink-600">User-scoped queries; foreign IDs return not found.</dd>
            </div>
            <div class="grid gap-2 py-4 sm:grid-cols-[11rem_1fr]">
              <dt class="font-medium">Encryption</dt>
              <dd class="text-ink-600">HTTPS in deployment; Argon2 password hashes.</dd>
            </div>
            <div class="grid gap-2 py-4 sm:grid-cols-[11rem_1fr]">
              <dt class="font-medium">No training by default</dt>
              <dd class="text-ink-600">Your documents power your answers — not a shared training corpus.</dd>
            </div>
            <div class="grid gap-2 py-4 sm:grid-cols-[11rem_1fr]">
              <dt class="font-medium">Model keys</dt>
              <dd class="text-ink-600">Server environment only. Not in the browser.</dd>
            </div>
          </dl>
          <div class="mt-8 flex flex-wrap gap-4 text-sm">
            <a routerLink="/privacy" class="font-medium text-accent-700 hover:underline">Privacy notes →</a>
            <a routerLink="/demo" class="font-medium text-accent-700 hover:underline">Try Live Demo →</a>
          </div>
        </div>
      </article>
      <app-site-footer></app-site-footer>
    </div>
  `,
})
export class SecurityComponent {}
