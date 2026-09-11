import { Component, inject } from '@angular/core';
import { NgIf } from '@angular/common';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { LucideMenu, LucideX } from '@lucide/angular';
import { LogoComponent } from './logo.component';
import { AuthService } from '../../core/services/auth.service';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-site-header',
  imports: [NgIf, RouterLink, RouterLinkActive, LogoComponent, LucideMenu, LucideX],
  template: `
    <header class="sticky top-0 z-50 border-b border-paper-200/80 bg-paper-50/90 backdrop-blur dark:border-white/10 dark:bg-ink-950/90">
      <div class="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3 sm:px-6">
        <app-logo></app-logo>
        <nav class="hidden items-center gap-4 xl:flex" aria-label="Product">
          <a class="nav-link" href="/#product">Product</a>
          <a class="nav-link" href="/#how">How It Works</a>
          <a class="nav-link" routerLink="/security" routerLinkActive="text-ink-950 dark:text-white">Security</a>
          <a class="nav-link" routerLink="/case-study" routerLinkActive="text-ink-950 dark:text-white">Case Study</a>
          <a class="nav-link" routerLink="/architecture" routerLinkActive="text-ink-950 dark:text-white">Architecture</a>
          <a class="nav-link" [href]="githubUrl" target="_blank" rel="noopener noreferrer">GitHub</a>
        </nav>
        <div class="hidden items-center gap-4 text-sm lg:flex">
          <ng-container *ngIf="auth.isLoggedIn; else guestActions">
            <a routerLink="/app" class="btn-ink">Open workspace</a>
          </ng-container>
          <ng-template #guestActions>
            <a routerLink="/login" routerLinkActive="text-ink-950 dark:text-white" class="nav-link">Sign in</a>
            <a routerLink="/demo" class="btn-ink">Try Live Demo</a>
          </ng-template>
        </div>
        <button class="rounded-md p-1 lg:hidden" type="button" (click)="open = !open" [attr.aria-expanded]="open" aria-label="Open menu">
          <svg *ngIf="!open" lucideMenu [size]="20"></svg>
          <svg *ngIf="open" lucideX [size]="20"></svg>
        </button>
      </div>
      <div *ngIf="open" class="space-y-1 border-t border-paper-200 px-6 py-4 text-sm lg:hidden dark:border-white/10">
        <a class="block py-2" href="/#product" (click)="open = false">Product</a>
        <a class="block py-2" href="/#how" (click)="open = false">How It Works</a>
        <a class="block py-2" routerLink="/security" (click)="open = false">Security</a>
        <a class="block py-2" routerLink="/case-study" (click)="open = false">Case Study</a>
        <a class="block py-2" routerLink="/architecture" (click)="open = false">Architecture</a>
        <a class="block py-2" [href]="githubUrl" target="_blank" rel="noopener noreferrer" (click)="open = false">GitHub</a>
        <a *ngIf="auth.isLoggedIn" class="btn-ink mt-3 w-full" routerLink="/app" (click)="open = false">Open workspace</a>
        <ng-container *ngIf="!auth.isLoggedIn">
          <a class="block py-2" routerLink="/login" (click)="open = false">Sign in</a>
          <a class="btn-ink mt-3 w-full" routerLink="/demo" (click)="open = false">Try Live Demo</a>
        </ng-container>
      </div>
    </header>
  `,
})
export class SiteHeaderComponent {
  readonly auth = inject(AuthService);
  readonly githubUrl = environment.githubUrl;
  open = false;
}
