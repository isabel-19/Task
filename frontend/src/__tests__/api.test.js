import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import { api, session, login, restoreSession, can, clearSession, query } from '../api';
beforeEach(() => {
  clearSession();
  vi.stubGlobal('fetch', vi.fn());
});
afterEach(() => vi.unstubAllGlobals());
describe('Sesión y transporte protegido', () => {
  it('mantiene el token en memoria y envía cookie y CSRF en las mutaciones', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        user: { id: 'demo' },
        permissions: ['tasks.write'],
        roles: ['integrante'],
        csrf_token: 'session-csrf',
        demo: true,
        has_real_participants: true,
        imported_participants: 4,
      }),
    });
    await login('demo@example.invalid', 'demo-password-123');
    expect(can('tasks.write')).toBe(true);
    expect(can('tasks.validate')).toBe(false);
    expect(session.realParticipants).toBe(true);
    expect(session.importedParticipants).toBe(4);
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({ id: 'task' }),
    });
    await api('/tasks', { method: 'POST', body: { title: 'Demo' } });
    const options = fetch.mock.calls[1][1];
    expect(options.credentials).toBe('include');
    expect(options.headers['X-CSRF-Token']).toBe('session-csrf');
    expect(JSON.parse(options.body)).toEqual({ title: 'Demo' });
  });
  it('restaura y descarta una sesión expirada', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Sesión expirada' }),
    });
    session.user = { id: 'old' };
    await restoreSession();
    expect(session.user).toBe(null);
    expect(session.csrf).toBe('');
    expect(session.ready).toBe(true);
  });
  it('presenta errores de campo sin esconder la validación del servidor', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [{ loc: ['due_date'], msg: 'Fecha inválida' }],
      }),
    });
    await expect(api('/tasks')).rejects.toThrow('Plazo: Fecha inválida');
  });
  it('preserva filtros válidos y descarta filtros vacíos', () => {
    expect(
      query({
        q: 'Carta múltiple',
        year: 2026,
        status: '',
        responsible_id: null,
      }),
    ).toBe('q=Carta+m%C3%BAltiple&year=2026');
  });
  it('envía archivos multipart con cookie y CSRF, sin forzar una cabecera JSON', async () => {
    session.csrf = 'csrf-file';
    const body = new FormData();
    body.append('file', new File(['evidencia'], 'informe.txt', { type: 'text/plain' }));
    fetch.mockResolvedValue({ ok: true, status: 200, json: async () => ({ id: 'task' }) });
    await api('/tasks/task/advance-file', { method: 'POST', body });
    const request = fetch.mock.calls[0][1];
    expect(request.body).toBe(body);
    expect(request.credentials).toBe('include');
    expect(request.headers['X-CSRF-Token']).toBe('csrf-file');
    expect(request.headers['Content-Type']).toBeUndefined();
  });
  it('obtiene la vista binaria por una solicitud autenticada y propaga los errores', async () => {
    const blob = new Blob(['%PDF-1.4'], { type: 'application/pdf' });
    fetch.mockResolvedValueOnce({ ok: true, status: 200, blob: async () => blob });
    expect(await api('/evidence-files/demo', { responseType: 'blob' })).toBe(blob);
    expect(fetch.mock.calls[0][1].credentials).toBe('include');
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'No tienes acceso' }),
    });
    await expect(api('/evidence-files/demo', { responseType: 'blob' })).rejects.toThrow(
      'No tienes acceso',
    );
  });
});
