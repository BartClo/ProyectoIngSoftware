const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

type RequestOptions = {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
};

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

export async function deleteConversation(conversationId: number) {
  return api(`/conversations/${conversationId}/`, { method: 'DELETE' });
}

export async function getConversations() {
  return api('/conversations/');
}

export async function getConversationMessages(conversationId: number) {
  return api(`/conversations/${conversationId}/messages/`);
}

export async function createConversation() {
  return api('/conversations/', { method: 'POST', body: { with_welcome: true } });
}
