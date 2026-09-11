import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { AuthShellComponent } from './auth-shell.component';
import { apiError } from '../../shared/utils';

@Component({
  selector: 'app-forgot-password',
  imports: [ReactiveFormsModule, RouterLink, NgIf, AuthShellComponent],
  template: `
    <app-auth-shell>
      <h1 class="font-display text-3xl tracking-tight">Forgot password</h1>
      <p class="mt-1 text-sm text-ink-600">We’ll send a reset link if an account exists for that email.</p>
      <form class="mt-6 space-y-4" [formGroup]="form" (ngSubmit)="submit()">
        <label class="block text-sm font-medium">Email
          <input class="field mt-1" type="email" formControlName="email" />
        </label>
        <p *ngIf="message" class="text-sm text-ink-600">{{ message }}</p>
        <p *ngIf="error" class="text-sm text-red-600">{{ error }}</p>
        <button class="btn-ink w-full disabled:opacity-50" [disabled]="form.invalid || loading">
          {{ loading ? 'Sending…' : 'Send reset link' }}
        </button>
      </form>
      <a routerLink="/login" class="mt-4 inline-block text-sm text-ink-600">Back to sign in</a>
    </app-auth-shell>
  `,
})
export class ForgotPasswordComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  loading = false;
  message = '';
  error = '';
  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = '';
    this.auth.forgotPassword(this.form.controls.email.value).subscribe({
      next: (res) => {
        this.loading = false;
        this.message = res.message;
      },
      error: (err) => {
        this.loading = false;
        this.error = apiError(err);
      },
    });
  }
}
