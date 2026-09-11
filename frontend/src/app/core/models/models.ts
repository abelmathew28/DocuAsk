export type SupportStatus = 'supported' | 'partially_supported' | 'not_found';

export interface User {
  id: string;
  name: string;
  email: string;
  theme: 'light' | 'dark' | 'system';
  default_model: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'failed';

export interface DocumentItem {
  id: string;
  name: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  document_type?: 'pdf' | 'docx' | 'txt';
  title?: string | null;
  page_count: number | null;
  status: DocumentStatus;
  processing_stage?: string | null;
  error_message: string | null;
  is_starred: boolean;
  summary: string | null;
  suggested_questions: string[];
  intelligence?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export type SearchScope = 'document' | 'selected' | 'library';
export type AskMode = 'ask' | 'research' | 'extract' | 'compare';

export interface SourceCitation {
  document: string;
  page: number;
  excerpt: string;
  relevance_score: number | null;
  chunk_id: string | null;
  document_id: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  feedback: 'up' | 'down' | null;
  created_at: string;
  sources: SourceCitation[];
  support_status?: SupportStatus | null;
}

export interface Conversation {
  id: string;
  document_id: string;
  document_name: string | null;
  title: string;
  preview: string | null;
  scope: SearchScope;
  document_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface ChatResponse {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
  answer: string;
  sources: SourceCitation[];
  support_status?: SupportStatus;
}

export interface DashboardStats {
  total_documents: number;
  questions_asked: number;
  conversations: number;
  storage_used: number;
  ai_requests: number;
  average_response_ms: number | null;
}

export interface AnalyticsSummary {
  documents_uploaded: number;
  questions_asked: number;
  total_conversations: number;
  ai_requests: number;
  average_response_time_ms: number | null;
}
