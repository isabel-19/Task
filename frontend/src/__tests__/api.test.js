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
    fetch.mockResolvedValueOnce({ ok: true, status: 201, json: async () => ({ id: 'task' }) });
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
      json: async () => ({ detail: [{ loc: ['due_date'], msg: 'Fecha inválida' }] }),
    });
    await expect(api('/tasks')).rejects.toThrow('due_date: Fecha inválida');
  });
  it('preserva filtros válidos y descarta filtros vacíos', () => {
    expect(query({ q: 'Carta múltiple', year: 2026, status: '', responsible_id: null })).toBe(
      'q=Carta+m%C3%BAltiple&year=2026',
    );
  });
});
