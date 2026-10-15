import { reactive } from 'vue';
import { formatApiError } from './format';

export const session = reactive({
  user: null,
  roles: [],
  permissions: [],
  csrf: '',
  demo: false,
  ready: false,
  importsEnabled: false,
  realParticipants: false,
  importedParticipants: 0,
});
const base = import.meta.env.DEV ? '/api' : import.meta.env.VITE_API_URL || '/api';

export function can(permission) {
  return Array.isArray(permission)
    ? permission.some(can)
    : session.permissions.includes(permission);
}

export async function api(path, options = {}) {
  const { responseType, ...requestOptions } = options;
  const multipart = options.body instanceof FormData;
  const response = await fetch(base + path, {
    ...requestOptions,
    credentials: 'include',
    headers: {
      ...(multipart ? {} : { 'Content-Type': 'application/json' }),
      'X-CSRF-Token': session.csrf,
      ...options.headers,
    },
    body:
      options.body === undefined
        ? undefined
        : multipart
          ? options.body
          : JSON.stringify(options.body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const details = data.detail;
    const message = formatApiError(details);
    if (response.status === 401) clearSession();
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return response.status === 204
    ? null
    : responseType === 'blob'
      ? response.blob()
      : response.json();
}

export function fileUrl(url) {
  return /^\/api\/evidence-files\/[a-f0-9-]+(?:\?download=true)?$/.test(url || '')
    ? base + url.slice(4)
    : url;
}

function setSession(data) {
  session.user = data.user;
  session.roles = data.roles;
  session.permissions = data.permissions;
  session.csrf = data.csrf_token;
  session.demo = data.demo;
  session.ready = true;
  session.importsEnabled = data.imports_enabled === true;
  session.realParticipants = data.has_real_participants === true;
  session.importedParticipants = data.imported_participants || 0;
}
export function clearSession() {
  session.user = null;
  session.roles = [];
  session.permissions = [];
  session.csrf = '';
  session.realParticipants = false;
  session.importedParticipants = 0;
  session.ready = true;
}
export async function restoreSession() {
  try {
    setSession(await api('/auth/me'));
  } catch (error) {
    if (error.status !== 401) throw error;
    clearSession();
  }
}
export async function login(email, password) {
  setSession(await api('/auth/login', { method: 'POST', body: { email, password } }));
}
export async function logout() {
  await api('/auth/logout', { method: 'POST' });
  clearSession();
}
export function query(values) {
  return new URLSearchParams(
    Object.entries(values).filter(([, v]) => v !== '' && v !== null && v !== undefined),
  ).toString();
}
export async function downloadReport(entity, filters = {}) {
  const response = await fetch(`${base}/reports/${entity}.csv?${query(filters)}`, {
    credentials: 'include',
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    if (response.status === 401) clearSession();
    throw new Error(formatApiError(err.detail));
  }
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `ogc-${entity}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
