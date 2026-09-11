import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { ChatResponse, Conversation, ConversationDetail, SearchScope } from '../models/models';

@Injectable({ providedIn: 'root' })
export class ConversationService {
  constructor(private readonly http: HttpClient) {}

  list(documentId?: string, scope?: SearchScope) {
    let params = new HttpParams();
    if (documentId) params = params.set('document_id', documentId);
    if (scope) params = params.set('scope', scope);
    return this.http.get<Conversation[]>(`${environment.apiUrl}/conversations`, { params });
  }

  get(id: string) {
    return this.http.get<ConversationDetail>(`${environment.apiUrl}/conversations/${id}`);
  }

  create(payload: { document_id?: string; document_ids?: string[]; scope?: SearchScope; title?: string }) {
    return this.http.post<ConversationDetail>(`${environment.apiUrl}/conversations`, payload);
  }

  rename(id: string, title: string) {
    return this.http.patch<Conversation>(`${environment.apiUrl}/conversations/${id}`, { title });
  }

  delete(id: string) {
    return this.http.delete<{ message: string }>(`${environment.apiUrl}/conversations/${id}`);
  }

  deleteAll() {
    return this.http.delete<{ message: string }>(`${environment.apiUrl}/users/me/conversations`);
  }

  sendMessage(id: string, content: string, mode: 'ask' | 'research' | 'extract' = 'ask') {
    return this.http.post<ChatResponse>(`${environment.apiUrl}/conversations/${id}/messages`, { content, mode });
  }

  regenerate(id: string) {
    return this.http.post<ChatResponse>(`${environment.apiUrl}/conversations/${id}/regenerate`, {});
  }

  feedback(conversationId: string, messageId: string, rating: 'up' | 'down') {
    return this.http.post(`${environment.apiUrl}/conversations/${conversationId}/messages/${messageId}/feedback`, {
      rating,
    });
  }

  exportMarkdown(id: string, title: string) {
    return this.http.get(`${environment.apiUrl}/conversations/${id}/export`, { responseType: 'blob' }).subscribe((blob) => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${title.replace(/\s+/g, '-').toLowerCase() || 'conversation'}.md`;
      link.click();
      URL.revokeObjectURL(url);
    });
  }
}
