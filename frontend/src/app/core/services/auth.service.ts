import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthResponse, User } from '../models/models';

const ACCESS_KEY = 'docuask.access';
const REFRESH_KEY = 'docuask.refresh';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly userSubject = new BehaviorSubject<User | null>(null);
  readonly user$ = this.userSubject.asObservable();

  constructor(
    private readonly http: HttpClient,
    private readonly router: Router
  ) {
    const token = this.accessToken;
    if (token) {
      this.loadMe().subscribe({ error: () => this.clearSession() });
    }
  }

  get accessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  }

  get refreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  get currentUser(): User | null {
    return this.userSubject.value;
  }

  get isLoggedIn(): boolean {
    return !!this.accessToken;
  }

  register(payload: { name: string; email: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/register`, payload).pipe(tap((res) => this.setSession(res)));
  }

  login(payload: { email: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/login`, payload).pipe(tap((res) => this.setSession(res)));
  }

  demoLogin(): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${environment.apiUrl}/auth/demo`, {}).pipe(tap((res) => this.setSession(res)));
  }

  logout(): void {
    const refresh = this.refreshToken;
    if (refresh) {
      this.http.post(`${environment.apiUrl}/auth/logout`, { refresh_token: refresh }).subscribe({
        complete: () => undefined,
        error: () => undefined,
      });
    }
    this.clearSession();
    void this.router.navigate(['/login']);
  }

  refresh(): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${environment.apiUrl}/auth/refresh`, { refresh_token: this.refreshToken })
      .pipe(tap((res) => this.setSession(res)));
  }

  forgotPassword(email: string) {
    return this.http.post<{ message: string }>(`${environment.apiUrl}/auth/forgot-password`, { email });
  }

  resetPassword(token: string, password: string) {
    return this.http.post<{ message: string }>(`${environment.apiUrl}/auth/reset-password`, { token, password });
  }

  changePassword(current_password: string, new_password: string) {
    return this.http.post<{ message: string }>(`${environment.apiUrl}/auth/change-password`, {
      current_password,
      new_password,
    });
  }

  loadMe() {
    return this.http.get<User>(`${environment.apiUrl}/auth/me`).pipe(tap((user) => this.userSubject.next(user)));
  }

  setSession(res: AuthResponse): void {
    localStorage.setItem(ACCESS_KEY, res.access_token);
    localStorage.setItem(REFRESH_KEY, res.refresh_token);
    this.userSubject.next(res.user);
  }

  clearSession(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    this.userSubject.next(null);
  }
}
