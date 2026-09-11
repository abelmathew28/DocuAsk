import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { DocumentItem, DocumentStatus } from '../models/models';

@Injectable({ providedIn: 'root' })
export class DocumentService {
  constructor(private readonly http: HttpClient) {}

  list(opts: { q?: string; status?: DocumentStatus | ''; sort?: string; order?: string; starred?: boolean } = {}) {
    let params = new HttpParams();
    if (opts.q) params = params.set('q', opts.q);
    if (opts.status) params = params.set('status', opts.status);
    if (opts.sort) params = params.set('sort', opts.sort);
    if (opts.order) params = params.set('order', opts.order);
    if (opts.starred) params = params.set('starred', 'true');
    return this.http.get<DocumentItem[]>(`${environment.apiUrl}/documents`, { params });
  }

  get(id: string) {
    return this.http.get<DocumentItem>(`${environment.apiUrl}/documents/${id}`);
  }

  status(id: string) {
    return this.http.get<{
      id: string;
      status: DocumentStatus;
      processing_stage: string | null;
      page_count: number | null;
      error_message: string | null;
    }>(`${environment.apiUrl}/documents/${id}/status`);
  }

  upload(file: File) {
    const data = new FormData();
    data.append('file', file, file.name);
    return this.http.post<DocumentItem>(`${environment.apiUrl}/documents`, data);
  }

  rename(id: string, name: string) {
    return this.http.patch<DocumentItem>(`${environment.apiUrl}/documents/${id}`, { name });
  }

  delete(id: string) {
    return this.http.delete<{ message: string }>(`${environment.apiUrl}/documents/${id}`);
  }

  star(id: string, is_starred: boolean) {
    return this.http.patch<DocumentItem>(`${environment.apiUrl}/documents/${id}`, { is_starred });
  }

  download(id: string, filename: string) {
    return this.http.get(`${environment.apiUrl}/documents/${id}/file`, {
      params: { download: true },
      responseType: 'blob',
    }).subscribe((blob) => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    });
  }

  fileUrl(id: string): string {
    return `${environment.apiUrl}/documents/${id}/file`;
  }

  reprocess(id: string) {
    return this.http.post<DocumentItem>(`${environment.apiUrl}/documents/${id}/reprocess`, {});
  }
}
