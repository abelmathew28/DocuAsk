import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { AnalyticsSummary, DashboardStats, User } from '../models/models';

@Injectable({ providedIn: 'root' })
export class UserService {
  constructor(private readonly http: HttpClient) {}

  stats() {
    return this.http.get<DashboardStats>(`${environment.apiUrl}/users/me/stats`);
  }

  analytics() {
    return this.http.get<AnalyticsSummary>(`${environment.apiUrl}/analytics/summary`);
  }

  update(payload: Partial<Pick<User, 'name' | 'theme' | 'default_model'>>) {
    return this.http.patch<User>(`${environment.apiUrl}/users/me`, payload);
  }

  deleteAccount() {
    return this.http.delete<{ message: string }>(`${environment.apiUrl}/users/me`);
  }
}
