import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { ToastService } from '../services/toast.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      const skip = req.url.includes('/auth/refresh') || req.url.includes('/auth/me');
      if (!skip && error.status !== 401) {
        const detail = error.error?.detail;
        const message = typeof detail === 'string' ? detail : 'Something went wrong. Please try again.';
        toast.error(message);
      }
      return throwError(() => error);
    })
  );
};
