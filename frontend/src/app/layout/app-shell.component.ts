import { Component, HostListener, inject, OnInit, signal } from '@angular/core';
import { NgFor, NgIf } from '@angular/common';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { filter } from 'rxjs';
import {
  LucideSearch,
  LucideMenu,
  LucideX,
  LucideSun,
  LucideMoon,
} from '@lucide/angular';
import { AuthService } from '../core/services/auth.service';
import { ThemeService } from '../core/services/theme.service';
import { LogoComponent } from '../shared/components/logo.component';
import { DocumentService } from '../core/services/document.service';
import { UserService } from '../core/services/user.service';
import { ToastService } from '../core/services/toast.service';
import { DocumentItem } from '../core/models/models';

@Component({
  selector: 'app-shell',
  imports: [
    NgIf,
    NgFor,
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    FormsModule,
    LogoComponent,
    LucideSearch,
    LucideMenu,
    LucideX,
    LucideSun,
    LucideMoon,
  ],
  templateUrl: './app-shell.component.html',
})
export class AppShellComponent implements OnInit {
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  private readonly documents = inject(DocumentService);
  private readonly users = inject(UserService);
  private readonly router = inject(Router);
  private readonly toast = inject(ToastService);

  query = '';
  menuOpen = false;
  profileOpen = false;
  paletteOpen = false;
  shortcutsOpen = false;
  uploading = false;
  results = signal<DocumentItem[]>([]);
  isChat = false;
  isHome = true;
  isFiles = false;
  pageLabel = 'Dashboard';

  ngOnInit(): void {
    this.auth.user$.subscribe((user) => this.theme.syncUser(user));
    this.syncRoute(this.router.url);
    this.router.events.pipe(filter((event) => event instanceof NavigationEnd)).subscribe((event) => {
      this.menuOpen = false;
      this.profileOpen = false;
      this.paletteOpen = false;
      this.results.set([]);
      this.query = '';
      this.syncRoute((event as NavigationEnd).urlAfterRedirects);
    });
  }

  search(): void {
    const q = this.query.trim();
    if (!q) {
      this.results.set([]);
      return;
    }
    this.documents.list({ q }).subscribe((items) => this.results.set(items.slice(0, 8)));
  }

  toggleTheme(): void {
    const next = this.theme.theme() === 'dark' ? 'light' : 'dark';
    this.theme.apply(next);
    this.users.update({ theme: next }).subscribe();
  }

  logout(): void {
    this.auth.logout();
  }

  openDocument(doc: DocumentItem): void {
    this.paletteOpen = false;
    void this.router.navigate(['/app/documents', doc.id]);
  }

  upload(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file || this.uploading) return;
    this.uploading = true;
    this.documents.upload(file).subscribe({
      next: () => {
        this.uploading = false;
        this.toast.success('Reading the document.');
        void this.router.navigate(['/app/documents']);
      },
      error: () => (this.uploading = false),
    });
  }

  @HostListener('document:click')
  closePopovers(): void {
    this.profileOpen = false;
  }

  @HostListener('document:keydown', ['$event'])
  onKey(event: KeyboardEvent): void {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      this.paletteOpen = !this.paletteOpen;
      this.query = '';
      this.results.set([]);
    }
    if (event.key === '?' && !this.isTyping(event)) {
      this.shortcutsOpen = !this.shortcutsOpen;
    }
    if (event.key === 'Escape') {
      this.paletteOpen = false;
      this.shortcutsOpen = false;
      this.menuOpen = false;
    }
  }

  private syncRoute(url: string): void {
    const path = url.split('?')[0];
    this.isChat = /\/app\/(chat|ask|research|compare|extract)/.test(path);
    this.isFiles = path.startsWith('/app/documents');
    this.isHome = path === '/app' || path === '/app/';
    if (this.isHome) this.pageLabel = 'Dashboard';
    else if (this.isFiles) this.pageLabel = 'Documents';
    else if (path.includes('/research')) this.pageLabel = 'Research';
    else if (path.includes('/compare')) this.pageLabel = 'Compare';
    else if (path.includes('/extract')) this.pageLabel = 'Extract';
    else if (this.isChat) this.pageLabel = 'Ask';
    else if (path.includes('/settings')) this.pageLabel = 'Settings';
    else if (path.includes('/recent')) this.pageLabel = 'Recent';
    else if (path.includes('/help')) this.pageLabel = 'Guide';
    else this.pageLabel = 'Workspace';
  }

  private isTyping(event: KeyboardEvent): boolean {
    const target = event.target as HTMLElement | null;
    return !!target && ['INPUT', 'TEXTAREA'].includes(target.tagName);
  }
}
