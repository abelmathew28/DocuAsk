import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-landing-security-teaser',
  imports: [RouterLink],
  template: `
    <section id="security" class="marketing-section scroll-mt-24 py-6 sm:py-8" aria-labelledby="security-teaser-heading">
      <div class="marketing-panel px-5 py-5 sm:px-6">
        <p class="eyebrow">Security</p>
        <h2 id="security-teaser-heading" class="mt-2 font-display text-2xl tracking-tight sm:text-3xl">
          Private by default
        </h2>
        <p class="mt-3 max-w-2xl text-sm leading-6 text-ink-600">
          Documents stay on your account. Lookups are scoped to the signed-in user. Model keys stay on the server.
        </p>
        <dl class="mt-8 grid gap-6 sm:grid-cols-2">
          <div>
            <dt class="font-medium">Private storage</dt>
            <dd class="mt-1 text-sm leading-6 text-ink-600">Files and indexes are owned by your account — not a shared pool.</dd>
          </div>
          <div>
            <dt class="font-medium">Access controls</dt>
            <dd class="mt-1 text-sm leading-6 text-ink-600">JWT sessions; every document and conversation load is filtered by user id.</dd>
          </div>
          <div>
            <dt class="font-medium">Encryption in transit</dt>
            <dd class="mt-1 text-sm leading-6 text-ink-600">HTTPS in deployment; passwords hashed with Argon2.</dd>
          </div>
          <div>
            <dt class="font-medium">No training by default</dt>
            <dd class="mt-1 text-sm leading-6 text-ink-600">Your uploads are for answering your questions — not presented as training data for a public model.</dd>
          </div>
        </dl>
        <a routerLink="/security" class="mt-8 inline-block text-sm font-medium text-accent-700 hover:underline">Read security details →</a>
      </div>
    </section>
  `,
})
export class LandingSecurityTeaserComponent {}
