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
import TasksView from '../views/TasksView.vue';
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
      component:
        m.path === '/'
          ? DashboardView
          : m.path === '/reportes'
            ? ReportsView
            : m.path === '/tareas'
              ? TasksView
              : ModuleView,
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
      if (module.path === '/tareas') {
        await vi.waitFor(() => expect(host.querySelector('tbody tr')).not.toBeNull());
        expect(host.querySelector('.module-tabs')).toBeNull();
        expect(host.textContent).not.toContain('Cierres autorizados');
        expect(host.textContent).not.toContain('Asignaciones');
        expect(host.querySelectorAll('thead th')).toHaveLength(7);
      } else if (module.resources.length) {
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
  it('la agenda consulta la semana visible, permite cambiarla y conserva el espacio personal', async () => {
    const { host } = await screen(modules.find((module) => module.path === '/tareas'));
    await vi.waitFor(() => expect(host.querySelector('tbody tr')).not.toBeNull());
    [...host.querySelectorAll('button')]
      .find((button) => button.textContent.includes('Agenda semanal'))
      .click();
    await vi.waitFor(() => expect(host.querySelectorAll('.agenda-day')).toHaveLength(7));
    const request = () =>
      new URL(
        api.mock.calls.filter(([path]) => path.startsWith('/tasks?')).at(-1)[0],
        'https://test.invalid',
      );
    const first = request();
    expect(first.searchParams.get('scope')).toBe('received');
    expect(first.searchParams.get('from')).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(first.searchParams.get('to')).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(first.searchParams.get('page_size')).toBe('100');
    host.querySelector('button[aria-label="Semana siguiente"]').click();
    await vi.waitFor(() =>
      expect(request().searchParams.get('from')).not.toBe(first.searchParams.get('from')),
    );
    [...host.querySelectorAll('button')]
      .find((button) => button.textContent.trim() === 'Hoy')
      .click();
    await vi.waitFor(() =>
      expect(request().searchParams.get('from')).toBe(first.searchParams.get('from')),
    );
    [...host.querySelectorAll('button')]
      .find((button) => button.textContent.includes('Lista'))
      .click();
    await vi.waitFor(() => expect(host.querySelector('tbody tr')).not.toBeNull());
    expect(request().searchParams.has('from')).toBe(false);
    expect(request().searchParams.get('page_size')).toBe('20');
  });
  it('abre las tareas recibidas y permite consultar las asignadas y las del equipo según permisos', async () => {
    const { host } = await screen(modules.find((m) => m.path === '/tareas'));
    await vi.waitFor(() => expect(host.querySelector('tbody tr')).not.toBeNull());
    expect(
      api.mock.calls.some(
        ([path]) => path.startsWith('/tasks?') && path.includes('scope=received'),
      ),
    ).toBe(true);
    for (const [label, scope] of [
      ['Tareas que asigné', 'assigned'],
      ['Todas las tareas', 'team'],
      ['Mis tareas', 'received'],
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
        (b) => b.textContent.trim() === 'Todas las tareas',
      ),
    ).toBe(false);
  });
  it('notifica evidencia pendiente, abre la tarea desde la campana y retira el aviso al revisarse', async () => {
    const { host, router } = await screen(modules.find((module) => module.path === '/tareas'));
    await vi.waitFor(() => expect(host.querySelector('tbody tr')).not.toBeNull());
    const original = api.getMockImplementation();
    const task = fixture.tasks.items[0];
    let pending = true;
    api.mockImplementation((path) =>
      path === '/alerts'
        ? Promise.resolve(
            pending
              ? [
                  {
                    id: 'aporte-pendiente',
                    task_id: task.id,
                    kind: 'task_review',
                    entity: 'tasks',
                    title: task.title,
                    author: 'Persona de prueba',
                    progress: 45,
                    label: 'Evidencia pendiente de revisión',
                    overdue: false,
                  },
                ]
              : [],
          )
        : original(path),
    );
    window.dispatchEvent(new Event('ogc:task-review-changed'));
    await vi.waitFor(() => expect(host.querySelector('.topbar .q-badge')?.textContent).toBe('1'));
    host.querySelector('button[aria-label="Ver alertas"]').click();
    await vi.waitFor(() =>
      expect(document.querySelector('.alerts-drawer')?.textContent).toContain('Persona de prueba'),
    );
    expect(document.querySelector('.alerts-drawer').textContent).toContain('Por revisar');
    document.querySelector('.alerts-drawer .q-item').click();
    await vi.waitFor(() => expect(router.currentRoute.value.query.id).toBe(task.id));
    expect(router.currentRoute.value.query.scope).toBe('review');
    expect(router.currentRoute.value.query.review).toBe('aporte-pendiente');
    await vi.waitFor(() =>
      expect(
        api.mock.calls.some(
          ([path]) =>
            path.startsWith('/tasks?') &&
            path.includes('pending_review=true') &&
            path.includes('scope=team'),
        ),
      ).toBe(true),
    );
    pending = false;
    window.dispatchEvent(new Event('ogc:task-review-changed'));
    await vi.waitFor(() => expect(host.querySelector('.topbar .q-badge')).toBeNull());
  });
});
