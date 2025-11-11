const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

type RequestOptions = {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
};

// Tipos para el sistema RAG
export interface ChatbotInfo {
  id: number;
  title: string;
  description: string;
  is_owner: boolean;
}

export interface ConversationDTO {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  chatbot_id?: number;
  chatbot_name?: string;
}

export interface MessageDTO {
  id: number;
  sender: 'user' | 'ai';
  text: string;
  created_at: string;
  sources?: string[];
}

export interface ChatResponseDTO {
  response: string;
  sources: string[];
  chatbot_used?: string;
  context_chunks: number;
}

export const getToken = () => typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
export const setToken = (t: string) => { if (typeof window !== 'undefined') localStorage.setItem('access_token', t); };

export async function api(path: string, opts: RequestOptions = {}) {
  const url = API_BASE + path;
  const headers: Record<string,string> = opts.headers ? { ...opts.headers } : {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  if (opts.body && !(opts.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.body);
  }

  const res = await fetch(url, { method: opts.method || 'GET', body: opts.body, headers });
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok) {
    let err = await res.text();
    try { err = JSON.parse(err); } catch {}
    throw { status: res.status, body: err };
  }

  // No content (204) -> resolver como null para evitar parsear body vacío
  if (res.status === 204 || res.status === 205) return null;

  // Si el servidor indica JSON pero el body viene vacío, leer como text y parsear con seguridad
  if (contentType.includes('application/json')) {
    const txt = await res.text();
    if (!txt) return null;
    return JSON.parse(txt);
  }

  return res.text();
}

export async function loginAPI(username: string, password: string) {
  // FastAPI expects form data for OAuth2PasswordRequestForm
  const body = new URLSearchParams();
  body.append('username', username);
  body.append('password', password);
  const url = API_BASE + '/login/';
  const res = await fetch(url, { method: 'POST', body });
  if (!res.ok) {
    const txt = await res.text();
    throw { status: res.status, body: txt };
  }
  const data = await res.json();
  if (data?.access_token) setToken(data.access_token);
  return data;
}

export async function fetchUsers() {
  return api('/admin/users/');
}

export async function createAdminUser(payload: { email: string; password: string; nombre?: string }) {
  return api('/admin/users/', { method: 'POST', body: payload });
}

export async function deleteAdminUser(userId: number) {
  return api(`/admin/users/${userId}/`, { method: 'DELETE' });
}

export async function updateUserPassword(userId: number, password: string) {
  return api(`/admin/users/${userId}/password`, { 
    method: 'PATCH', 
    body: { password } 
  });
}

export async function createConversationAdmin(form: FormData) {
  // send multipart/form-data to /admin/conversations/
  const url = API_BASE + '/admin/conversations/';
  const token = getToken();
  const headers: Record<string,string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(url, { method: 'POST', body: form, headers });
  if (!res.ok) throw { status: res.status, body: await res.text() };
  return res.json();
}

export async function listAdminConversations() {
  return api('/admin/conversations/');
}

export async function deleteAdminConversation(conversationId: number) {
  return api(`/admin/conversations/${conversationId}/`, { method: 'DELETE' });
}

export async function uploadConversationAttachments(conversationId: number, form: FormData) {
  const url = API_BASE + `/conversations/${conversationId}/attachments/`;
  const token = getToken();
  const headers: Record<string,string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(url, { method: 'POST', body: form, headers });
  if (!res.ok) throw { status: res.status, body: await res.text() };
  return res.json();
}

export async function createReport(payload: { report_type: string; comment?: string; conversation_id?: number }) {
  return api('/reports/', { method: 'POST', body: payload });
}

export async function listAdminReports() {
  return api('/admin/reports/');
}

// ===== CONVERSATIONS API (Sistema RAG) =====
export async function listConversations() {
  return api('/api/chat/conversations');
}

export async function createConversation(data: { title?: string; chatbot_id?: number; with_welcome?: boolean } = {}) {
  return api('/api/chat/conversations', { 
    method: 'POST', 
    body: { with_welcome: true, ...data } 
  });
}

export async function renameConversation(id: number, title: string) {
  return api(`/api/chat/conversations/${id}`, { 
    method: 'PATCH', 
    body: { title } 
  });
}

export async function deleteConversation(conversationId: number) {
  return api(`/api/chat/conversations/${conversationId}`, { method: 'DELETE' });
}

export async function listMessages(conversationId: number) {
  return api(`/api/chat/conversations/${conversationId}/messages`);
}

export async function sendMessage(conversationId: number, text: string, chatbotId?: number) {
  return api(`/api/chat/conversations/${conversationId}/messages`, { 
    method: 'POST', 
    body: { text, chatbot_id: chatbotId } 
  });
}

// ===== CHATBOTS API =====
export async function createChatbot(data: { title: string; description?: string }) {
  return api('/api/chatbots/', { method: 'POST', body: data });
}

export async function listUserChatbots() {
  return api('/api/chatbots/');
}

export async function getChatbot(chatbotId: number) {
  return api(`/api/chatbots/${chatbotId}`);
}

export async function updateChatbot(chatbotId: number, data: { title?: string; description?: string; is_active?: boolean }) {
  return api(`/api/chatbots/${chatbotId}`, { method: 'PUT', body: data });
}

export async function deleteChatbot(chatbotId: number) {
  return api(`/api/chatbots/${chatbotId}`, { method: 'DELETE' });
}

export async function grantUserAccess(chatbotId: number, data: { user_ids: number[]; access_level?: 'read' | 'write' | 'admin' }) {
  return api(`/api/chatbots/${chatbotId}/users`, { method: 'POST', body: data });
}

export async function listChatbotUsers(chatbotId: number) {
  return api(`/api/chatbots/${chatbotId}/users`);
}

export async function revokeChatbotAccess(chatbotId: number, userId: number) {
  return api(`/api/chatbots/${chatbotId}/users/${userId}`, { method: 'DELETE' });
}

export async function getChatbotStats(chatbotId: number) {
  return api(`/api/chatbots/${chatbotId}/stats`);
}

// ===== DOCUMENTS API =====
export async function uploadDocuments(chatbotId: number, files: FileList | File[]) {
  const formData = new FormData();
  Array.from(files).forEach(file => {
    formData.append('files', file);
  });
  
  const url = API_BASE + `/api/chatbots/${chatbotId}/documents/upload`;
  const token = getToken();
  const headers: Record<string,string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  const res = await fetch(url, { method: 'POST', body: formData, headers });
  if (!res.ok) throw { status: res.status, body: await res.text() };
  return res.json();
}

export async function listChatbotDocuments(chatbotId: number) {
  return api(`/api/chatbots/${chatbotId}/documents/`);
}

export async function deleteChatbotDocument(chatbotId: number, documentId: number) {
  return api(`/api/chatbots/${chatbotId}/documents/${documentId}`, { method: 'DELETE' });
}

export async function processDocuments(chatbotId: number) {
  return api(`/api/chatbots/${chatbotId}/documents/process`, { method: 'POST' });
}

export async function getDocumentStatus(chatbotId: number, documentId: number) {
  return api(`/api/chatbots/${chatbotId}/documents/${documentId}/status`);
}

// ===== RAG CHAT API =====
export async function sendRagMessage(text: string, chatbotId?: number) {
  return api('/api/chat/message', { 
    method: 'POST', 
    body: { text, chatbot_id: chatbotId } 
  });
}

export async function getAvailableChatbots() {
  return api('/api/chat/available-chatbots');
}
