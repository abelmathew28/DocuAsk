import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { UserService } from '../../core/services/user.service';
import { ConversationService } from '../../core/services/conversation.service';
import { ThemeService } from '../../core/services/theme.service';
import { ToastService } from '../../core/services/toast.service';
import { ConfirmDialogComponent } from '../../shared/components/confirm-dialog.component';
import { AnalyticsSummary, User } from '../../core/models/models';

@Component({
  selector: 'app-settings',
  imports: [FormsModule, ConfirmDialogComponent],
  templateUrl: './settings.component.html',
})
export class SettingsComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly users = inject(UserService);
  private readonly conversations = inject(ConversationService);
  private readonly theme = inject(ThemeService);
  private readonly toast = inject(ToastService);

  user = signal<User | null>(this.auth.currentUser);
  analytics = signal<AnalyticsSummary | null>(null);
  name = this.auth.currentUser?.name || '';
  themeValue: 'light' | 'dark' | 'system' = this.auth.currentUser?.theme || 'system';
  currentPassword = '';
  newPassword = '';
  confirmDeleteConversations = false;
  confirmDeleteAccount = false;

  ngOnInit(): void {
    this.auth.loadMe().subscribe((user) => {
      this.user.set(user);
      this.name = user.name;
      this.themeValue = user.theme;
    });
    this.users.analytics().subscribe((data) => this.analytics.set(data));
  }

  saveProfile(): void {
    this.users.update({ name: this.name, theme: this.themeValue }).subscribe((user) => {
      this.user.set(user);
      this.theme.apply(user.theme);
      this.toast.success('Profile updated.');
    });
  }

  changePassword(): void {
    if (this.newPassword.length < 8) return;
    this.auth.changePassword(this.currentPassword, this.newPassword).subscribe(() => {
      this.currentPassword = '';
      this.newPassword = '';
      this.toast.success('Password updated.');
    });
  }

  deleteConversations(): void {
    this.conversations.deleteAll().subscribe(() => {
      this.confirmDeleteConversations = false;
      this.toast.success('Conversations deleted.');
      this.users.analytics().subscribe((data) => this.analytics.set(data));
    });
  }

  deleteAccount(): void {
    this.users.deleteAccount().subscribe(() => this.auth.logout());
  }
}
