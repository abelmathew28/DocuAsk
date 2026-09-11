import { Injectable, signal } from '@angular/core';
import { User } from '../models/models';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<'light' | 'dark' | 'system'>('system');

  constructor() {
    const stored = (localStorage.getItem('docuask.theme') as 'light' | 'dark' | 'system' | null) ?? 'system';
    this.apply(stored);
  }

  apply(theme: 'light' | 'dark' | 'system'): void {
    this.theme.set(theme);
    localStorage.setItem('docuask.theme', theme);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const dark = theme === 'dark' || (theme === 'system' && prefersDark);
    document.documentElement.classList.toggle('dark', dark);
  }

  syncUser(user: User | null): void {
    if (user?.theme) {
      this.apply(user.theme);
    }
  }
}
