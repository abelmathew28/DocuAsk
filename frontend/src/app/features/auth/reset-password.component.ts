import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { NgIf } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { AuthShellComponent } from './auth-shell.component';
import { apiError } from '../../shared/utils';

@Component({
  selector: 'app-reset-password',
  imports: [ReactiveFormsModule, RouterLink, NgIf, AuthShellComponent],
  template: `
    <app-auth-shell>
      <h1 class="font-display text-3xl tracking-tight">Reset password</h1>
      <form class="mt-6 space-y-4" [formGroup]="form" (ngSubmit)="submit()">
        <label class="block text-sm font-medium">New password
          <input class="field mt-1" type="password" formControlName="password" autocomplete="new-password" />
        </label>
        <p *ngIf="error" class="text-sm text-red-600">{{ error }}</p>
        <button class="btn-ink w-full disabled:opacity-50" [disabled]="form.invalid || loading || !token">
          {{ loading ? 'Updating…' : 'Update password' }}
        </button>
      </form>
      <a routerLink="/login" class="mt-4 inline-block text-sm text-ink-600">Back to sign in</a>
    </app-auth-shell>
  `,
})
export class ResetPasswordComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  token = inject(ActivatedRoute).snapshot.queryParamMap.get('token') || '';
  loading = false;
  error = '';
  form = this.fb.nonNullable.group({
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submit(): void {
    if (this.form.invalid || !this.token) return;
    this.loading = true;
    this.auth.resetPassword(this.token, this.form.controls.password.value).subscribe({
      next: () => this.router.navigateByUrl('/login'),
      error: (err) => {
        this.loading = false;
        this.error = apiError(err, 'This reset link is invalid or has expired.');
      },
    });
  }
}
