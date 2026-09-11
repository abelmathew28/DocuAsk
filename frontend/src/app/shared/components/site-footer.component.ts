import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-site-footer',
  imports: [RouterLink],
  template: `
    <footer class="border-t border-paper-200 dark:border-white/10">
      <div class="mx-auto flex max-w-6xl flex-col gap-6 px-5 py-8 sm:flex-row sm:justify-between sm:px-6">
        <div>
          <p class="font-display text-xl">DocuAsk</p>
          <p class="mt-2 max-w-xs text-sm leading-6 text-ink-600">
            Ask your documents. Verify every answer.
          </p>
        </div>
        <nav class="flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-600" aria-label="Footer">
          <a class="hover:text-ink-950 dark:hover:text-white" href="/#product">Product</a>
          <a class="hover:text-ink-950 dark:hover:text-white" href="/#how">How It Works</a>
          <a class="hover:text-ink-950 dark:hover:text-white" routerLink="/security">Security</a>
          <a class="hover:text-ink-950 dark:hover:text-white" routerLink="/case-study">Case Study</a>
          <a class="hover:text-ink-950 dark:hover:text-white" [href]="githubUrl" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a class="hover:text-ink-950 dark:hover:text-white" routerLink="/privacy">Privacy</a>
          <a class="hover:text-ink-950 dark:hover:text-white" routerLink="/demo">Try Live Demo</a>
        </nav>
      </div>
    </footer>
  `,
})
export class SiteFooterComponent {
  readonly githubUrl = environment.githubUrl;
}
