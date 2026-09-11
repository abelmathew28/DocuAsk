import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [{ provide: Router, useValue: { navigate: () => undefined } }],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  it('stores tokens after login', () => {
    service.login({ email: 'abel@example.com', password: 'password123' }).subscribe();
    const req = http.expectOne(`${environment.apiUrl}/auth/login`);
    req.flush({
      access_token: 'a',
      refresh_token: 'r',
      token_type: 'bearer',
      user: { id: '1', name: 'Abel', email: 'abel@example.com', theme: 'system', default_model: null, created_at: '' },
    });
    expect(service.accessToken).toBe('a');
    expect(service.currentUser?.name).toBe('Abel');
  });
});
