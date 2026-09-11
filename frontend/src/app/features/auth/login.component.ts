import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';
import { LucideEye, LucideEyeOff } from '@lucide/angular';
import { AuthService } from '../../core/services/auth.service';
import { AuthShellComponent } from './auth-shell.component';
import { apiError } from '../../shared/utils';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, RouterLink, NgIf, AuthShellComponent, LucideEye, LucideEyeOff],
  template: `
    <app-auth-shell>
      <h1 class="font-display text-3xl tracking-tight">Sign in</h1>
      <p class="mt-2 text-sm text-ink-600">Ask questions. Get answers you can verify.</p>
      <div *ngIf="demo" class="mt-6 border-y border-paper-200 py-4 text-sm dark:border-white/10">
        <p class="text-xs text-ink-600">Demo account</p>
        <p class="mt-1">{{ demo.email }}</p>
        <p class="text-ink-600">{{ demo.password }}</p>
        <button type="button" class="mt-3 text-sm underline underline-offset-4" (click)="useDemo()">Use this account</button>
      </div>
      <form class="mt-6 space-y-4" [formGroup]="form" (ngSubmit)="submit()">
        <label class="block text-sm">Email
          <input class="field mt-1" type="email" formControlName="email" autocomplete="email" />
        </label>
        <label class="block text-sm">Password
          <span class="relative mt-1 block">
            <input class="field pr-10" [type]="show ? 'text' : 'password'" formControlName="password" autocomplete="current-password" />
            <button type="button" class="absolute right-2 top-1/2 -translate-y-1/2 text-ink-600" (click)="show = !show" [attr.aria-label]="show ? 'Hide password' : 'Show password'">
              <svg *ngIf="!show" lucideEye [size]="16"></svg>
              <svg *ngIf="show" lucideEyeOff [size]="16"></svg>
            </button>
          </span>
        </label>
        <p *ngIf="error" class="text-sm text-red-600">{{ error }}</p>
        <button class="btn-ink mt-2 w-full disabled:opacity-50" [disabled]="form.invalid || loading">
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
      <div class="mt-5 flex justify-between text-sm text-ink-600">
        <a routerLink="/forgot-password">Forgot password</a>
        <a routerLink="/register">Create an account</a>
      </div>
    </app-auth-shell>
  `,
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly demo = environment.demoAccount;
  show = false;
  loading = false;
  error = '';
  form = this.fb.nonNullable.group({
    email: [this.demo?.email || '', [Validators.required, Validators.email]],
    password: [this.demo?.password || '', [Validators.required, Validators.minLength(8)]],
  });

  useDemo(): void {
    if (!this.demo) return;
    this.form.patchValue({ email: this.demo.email, password: this.demo.password });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';
    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => this.router.navigateByUrl('/app'),
      error: (err) => {
        this.loading = false;
        this.error = apiError(err, 'Invalid email or password.');
      },
    });
  }
}
