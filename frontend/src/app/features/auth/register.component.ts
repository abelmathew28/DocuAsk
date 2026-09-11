import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';
import { LucideEye, LucideEyeOff } from '@lucide/angular';
import { AuthService } from '../../core/services/auth.service';
import { AuthShellComponent } from './auth-shell.component';
import { apiError } from '../../shared/utils';

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink, NgIf, AuthShellComponent, LucideEye, LucideEyeOff],
  template: `
    <app-auth-shell>
      <h1 class="font-display text-3xl tracking-tight">Create an account</h1>
      <p class="mt-2 text-sm leading-6 text-ink-600">Upload a document, then ask a question you can check on the source page.</p>
      <form class="mt-8 space-y-4" [formGroup]="form" (ngSubmit)="submit()">
        <label class="block text-sm">Name
          <input class="field mt-1" formControlName="name" autocomplete="name" />
        </label>
        <label class="block text-sm">Email
          <input class="field mt-1" type="email" formControlName="email" autocomplete="email" />
        </label>
        <label class="block text-sm">Password
          <span class="relative mt-1 block">
            <input class="field pr-10" [type]="show ? 'text' : 'password'" formControlName="password" autocomplete="new-password" />
            <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-ink-600" (click)="show = !show" [attr.aria-label]="show ? 'Hide password' : 'Show password'">
              <svg *ngIf="!show" lucideEye [size]="16"></svg>
              <svg *ngIf="show" lucideEyeOff [size]="16"></svg>
            </button>
          </span>
        </label>
        <p *ngIf="error" class="text-sm text-red-600">{{ error }}</p>
        <button class="btn-ink mt-2 w-full disabled:opacity-50" [disabled]="form.invalid || loading">
          {{ loading ? 'Creating account…' : 'Create account' }}
        </button>
      </form>
      <p class="mt-5 text-sm text-ink-600">Already have an account? <a routerLink="/login" class="text-ink-950 underline underline-offset-4 dark:text-paper-50">Sign in</a></p>
    </app-auth-shell>
  `,
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  show = false;
  loading = false;
  error = '';
  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(1)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';
    this.auth.register(this.form.getRawValue()).subscribe({
      next: () => this.router.navigateByUrl('/app'),
      error: (err) => {
        this.loading = false;
        this.error = apiError(err, 'Unable to create account.');
      },
    });
  }
}
