import { Component } from '@angular/core';
import { SiteHeaderComponent } from '../../shared/components/site-header.component';
import { SiteFooterComponent } from '../../shared/components/site-footer.component';

@Component({
  selector: 'app-auth-shell',
  imports: [SiteHeaderComponent, SiteFooterComponent],
  template: `
    <div class="flex min-h-screen flex-col bg-paper-50 text-ink-950 dark:bg-ink-950 dark:text-paper-50">
      <app-site-header></app-site-header>
      <main class="mx-auto w-full max-w-sm flex-1 px-6 py-16">
        <ng-content></ng-content>
      </main>
      <app-site-footer></app-site-footer>
    </div>
  `,
})
export class AuthShellComponent {}
