// Centralized API client for backend integration
// Handles auth token, base URL, and typed endpoints for conversations and messages

export const API_BASE_URL: string = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

function getAuthToken(): string | null {
  return localStorage.getItem('authToken');
}

function buildHeaders(json: boolean = true): HeadersInit {
  const token = getAuthToken();
  const headers: Record<string, string> = {};
  if (json) headers['Content-Type'] = 'application/json';
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data?.detail) message = Array.isArray(data.detail) ? data.detail.map((d: any) => d.msg || d).join(', ') : String(data.detail);
      if (data?.error) message = String(data.error);
    } catch {}
    throw new Error(message);
  }
  return res.status === 204 ? (undefined as unknown as T) : await res.json();
}

// DTOs (backend response models)
export interface ConversationDTO {
  id: number;
  title: string;
  created_at: string; // ISO
  updated_at: string; // ISO
}

export interface MessageDTO {
  id: number;
  sender: 'user' | 'ai';
  text: string;
  created_at: string; // ISO
}

export interface ChatResponseDTO {
  response: string;
  sources: string[];
}

// Conversations
export async function listConversations(): Promise<ConversationDTO[]> {
  const res = await fetch(`${API_BASE_URL}/conversations/`, {
    method: 'GET',
    headers: buildHeaders(false),
  });
  return handleResponse<ConversationDTO[]>(res);
}

export async function createConversation(payload: { title?: string; with_welcome?: boolean } = {}): Promise<ConversationDTO> {
  const res = await fetch(`${API_BASE_URL}/conversations/`, {
    method: 'POST',
    headers: buildHeaders(true),
    body: JSON.stringify({ with_welcome: true, ...payload }),
  });
  return handleResponse<ConversationDTO>(res);
}

export async function renameConversation(id: number, title: string): Promise<ConversationDTO> {
  const res = await fetch(`${API_BASE_URL}/conversations/${id}/`, {
    method: 'PATCH',
    headers: buildHeaders(true),
    body: JSON.stringify({ title }),
  });
  return handleResponse<ConversationDTO>(res);
}

export async function deleteConversation(id: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/conversations/${id}/`, {
    method: 'DELETE',
    headers: buildHeaders(false),
  });
  return handleResponse<void>(res);
}

// Messages
export async function listMessages(conversationId: number): Promise<MessageDTO[]> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages/`, {
    method: 'GET',
    headers: buildHeaders(false),
  });
  return handleResponse<MessageDTO[]>(res);
}

export async function sendMessage(conversationId: number, text: string): Promise<ChatResponseDTO> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}/messages/`, {
    method: 'POST',
    headers: buildHeaders(true),
    body: JSON.stringify({ text }),
  });
  return handleResponse<ChatResponseDTO>(res);
}
