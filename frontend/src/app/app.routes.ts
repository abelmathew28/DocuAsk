import { Routes } from '@angular/router';
import { authGuard, guestGuard } from './core/guards/auth.guard';

const chatLoader = () => import('./features/chat/chat.component').then((m) => m.ChatComponent);
const documentsLoader = () => import('./features/documents/documents.component').then((m) => m.DocumentsComponent);

export const routes: Routes = [
  { path: '', loadComponent: () => import('./features/landing/landing.component').then((m) => m.LandingComponent) },
  { path: 'demo', loadComponent: () => import('./features/auth/demo-entry.component').then((m) => m.DemoEntryComponent) },
  { path: 'privacy', loadComponent: () => import('./features/landing/privacy.component').then((m) => m.PrivacyComponent) },
  { path: 'use-cases', loadComponent: () => import('./features/landing/use-cases.component').then((m) => m.UseCasesComponent) },
  { path: 'security', loadComponent: () => import('./features/landing/security.component').then((m) => m.SecurityComponent) },
  { path: 'case-study', loadComponent: () => import('./features/landing/case-study.component').then((m) => m.CaseStudyComponent) },
  {
    path: 'architecture',
    loadComponent: () => import('./features/landing/architecture.component').then((m) => m.ArchitectureComponent),
  },
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/register.component').then((m) => m.RegisterComponent),
  },
  { path: 'signup', redirectTo: 'register', pathMatch: 'full' },
  {
    path: 'forgot-password',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/forgot-password.component').then((m) => m.ForgotPasswordComponent),
  },
  {
    path: 'reset-password',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/reset-password.component').then((m) => m.ResetPasswordComponent),
  },
  {
    path: 'app',
    canActivate: [authGuard],
    loadComponent: () => import('./layout/app-shell.component').then((m) => m.AppShellComponent),
    children: [
      { path: '', loadComponent: () => import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent) },
      { path: 'dashboard', redirectTo: '', pathMatch: 'full' },
      { path: 'documents', loadComponent: documentsLoader },
      { path: 'documents/:id', loadComponent: documentsLoader },
      { path: 'chat', loadComponent: chatLoader },
      { path: 'chat/:id', loadComponent: chatLoader },
      { path: 'ask', loadComponent: chatLoader, data: { mode: 'ask' } },
      { path: 'ask/:id', loadComponent: chatLoader, data: { mode: 'ask' } },
      { path: 'research', loadComponent: chatLoader, data: { mode: 'research' } },
      { path: 'compare', loadComponent: chatLoader, data: { mode: 'compare' } },
      { path: 'extract', loadComponent: chatLoader, data: { mode: 'extract' } },
      { path: 'recent', loadComponent: () => import('./features/dashboard/recent.component').then((m) => m.RecentComponent) },
      { path: 'help', loadComponent: () => import('./features/help/help.component').then((m) => m.HelpComponent) },
      { path: 'settings', loadComponent: () => import('./features/settings/settings.component').then((m) => m.SettingsComponent) },
    ],
  },
  { path: '**', redirectTo: '' },
];
