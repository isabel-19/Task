import { createApp, nextTick } from 'vue';
import { Quasar, Notify, Dialog } from 'quasar';
import { createMemoryHistory, createRouter } from 'vue-router';
import { describe, it, expect, vi, afterEach } from 'vitest';
import fixture from './fixtures.json';
import { modules } from '../modules';
import App from '../App.vue';
import DashboardView from '../views/DashboardView.vue';
import ModuleView from '../views/ModuleView.vue';
import ReportsView from '../views/ReportsView.vue';
vi.mock('../api', async (importOriginal) => ({ ...(await importOriginal()), api: vi.fn() }));
import { api, session } from '../api';
const mounted = [];

async function screen(module) {
  session.user = fixture.users.items.find((u) => u.email === 'admin@example.invalid');
  session.roles = ['administrador'];
  session.ready = true;
  session.demo = true;
  session.importsEnabled = true;
  session.permissions = [
    ...new Set(
      Object.values(fixture.meta).flatMap((s) =>
        ['read', 'write', 'validate'].map((a) => s.module + '.' + a),
      ),
    ),
    'reports.read',
  ];
  api.mockImplementation((path) => {
    const url = new URL(path, 'https://test.invalid');
    const [resource, id] = url.pathname.slice(1).split('/');
    const data = fixture[resource];
    return Promise.resolve(id && data?.items ? data.items.find((i) => i.id === id) : data);
  });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: modules.map((m) => ({
      path: m.path,
      meta: m,
      component: m.path === '/' ? DashboardView : m.path === '/reportes' ? ReportsView : ModuleView,
    })),
  });
  await router.push(module.path);
  await router.isReady();
  const host = document.createElement('div');
  document.body.appendChild(host);
  const app = createApp(App).use(Quasar, { plugins: { Notify, Dialog } }).use(router);
  app.mount(host);
  mounted.push({ app, host });
  await nextTick();
  return { host, router };
}

afterEach(() => {
  for (const { app, host } of mounted.splice(0)) {
    app.unmount();
    host.remove();
  }
  document.body.innerHTML = '';
  vi.clearAllMocks();
});

describe('Once pantallas con el contrato real de la API de demostración', () => {
  it.each(modules.map((m) => [m.label, m]))(
    'abre %s y conserva el menú conectado',
    async (label, module) => {
      const { host } = await screen(module);
      await vi.waitFor(() =>
        expect(host.querySelector('.page-heading h1')?.textContent).toContain(
          module.path === '/' ? 'Panel de seguimiento' : label,
        ),
      );
      await vi.waitFor(() => expect(host.querySelectorAll('.nav-list .q-item')).toHaveLength(11));
      if (module.resources.length) {
        await vi.waitFor(() =>
          expect(host.querySelectorAll('.module-tabs>button:not(.q-btn)').length).toBe(
            module.resources.length,
          ),
        );
        expect(
          api.mock.calls.some(([path]) => path.startsWith('/' + module.resources[0] + '?')),
        ).toBe(true);
        if (fixture[module.resources[0]].items.length)
          await vi.waitFor(() =>
            expect(host.querySelectorAll('tbody tr').length).toBeGreaterThan(0),
          );
      } else if (module.path === '/') {
        await vi.waitFor(() => expect(host.querySelectorAll('.metric-card')).toHaveLength(4));
      } else {
        await vi.waitFor(() =>
          expect(host.querySelectorAll('.report-card').length).toBeGreaterThan(0),
        );
      }
    },
  );
  it('muestra un error recuperable al fallar el listado de tareas', async () => {
    const module = modules.find((m) => m.path === '/tareas');
    const { host } = await screen(module);
    await vi.waitFor(() => expect(host.querySelector('tbody tr')).not.toBeNull());
    api.mockImplementation((path) =>
      path.startsWith('/tasks?')
        ? Promise.reject(new Error('Servicio temporalmente no disponible'))
        : Promise.resolve(fixture[path.slice(1)]),
    );
    const refresh = [...host.querySelectorAll('button')].find(
      (b) => b.getAttribute('aria-label') === 'Actualizar listado',
    );
    refresh.click();
    await vi.waitFor(() =>
      expect(host.querySelector('[role=alert]').textContent).toContain(
        'Servicio temporalmente no disponible',
      ),
    );
    expect(host.querySelector('[role=alert]').textContent).toContain('Reintentar');
  });
  it('filtra mi espacio y permite al jefe consultar el equipo', async () => {
    const { host } = await screen(modules.find((m) => m.path === '/tareas'));
    await vi.waitFor(() => expect(host.querySelector('tbody tr')).not.toBeNull());
    expect(
      api.mock.calls.some(
        ([path]) => path.startsWith('/tasks?') && path.includes('scope=personal'),
      ),
    ).toBe(true);
    for (const [label, scope] of [
      ['Me asignaron', 'received'],
      ['Asigné', 'assigned'],
      ['En conjunto', 'joint'],
      ['Equipo', 'team'],
    ]) {
      [...host.querySelectorAll('.segmented button')]
        .find((b) => b.textContent.trim() === label)
        .click();
      await vi.waitFor(() =>
        expect(
          api.mock.calls.some(
            ([path]) => path.startsWith('/tasks?') && path.includes('scope=' + scope),
          ),
        ).toBe(true),
      );
    }
    session.permissions = ['tasks.read', 'tasks.write', 'reports.read'];
    await nextTick();
    expect(
      [...host.querySelectorAll('.segmented button')].some(
        (b) => b.textContent.trim() === 'Equipo',
      ),
    ).toBe(false);
  });
});
