import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { ChatResponse } from '../models/models';

@Injectable({ providedIn: 'root' })
export class IntelligenceService {
  constructor(private readonly http: HttpClient) {}

  research(payload: { question: string; document_ids?: string[]; conversation_id?: string }) {
    return this.http.post<ChatResponse>(`${environment.apiUrl}/research`, payload);
  }

  compare(payload: { document_a_id: string; document_b_id: string; question?: string; conversation_id?: string }) {
    return this.http.post<ChatResponse>(`${environment.apiUrl}/compare`, payload);
  }

  extract(payload: { question: string; document_ids?: string[]; fields?: string[]; conversation_id?: string }) {
    return this.http.post<ChatResponse>(`${environment.apiUrl}/extract`, payload);
  }

  summarize(payload: { kind?: string; document_ids?: string[]; focus?: string; conversation_id?: string }) {
    return this.http.post<ChatResponse>(`${environment.apiUrl}/summarize`, payload);
  }

  exportExtractCsv(documentIds: string[], fields: string[] = []) {
    const params = new URLSearchParams();
    if (documentIds.length) params.set('document_ids', documentIds.join(','));
    if (fields.length) params.set('fields', fields.join(','));
    params.set('fmt', 'csv');
    return this.http.get(`${environment.apiUrl}/extract/export?${params.toString()}`, {
      responseType: 'text',
    });
  }
}
