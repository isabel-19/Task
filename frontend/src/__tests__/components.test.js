import { createApp, nextTick, h } from 'vue';
import { Quasar, QLayout, QPageContainer } from 'quasar';
import { afterEach, describe, expect, it, vi } from 'vitest';
import StatusBadge from '../components/StatusBadge.vue';
import RecordForm from '../components/RecordForm.vue';
import ActionForm from '../components/ActionForm.vue';
import GanttChart from '../components/GanttChart.vue';
import DashboardView from '../views/DashboardView.vue';
import RecordDetail from '../components/RecordDetail.vue';
import fixture from './fixtures.json';
import { createRouter, createMemoryHistory } from 'vue-router';
vi.mock('../api', async (importOriginal) => ({ ...(await importOriginal()), api: vi.fn() }));
import { api } from '../api';
const apps = [];
function mount(component, props = {}, router) {
  const host = document.createElement('div');
  document.body.appendChild(host);
  const app = createApp(component, props);
  app.use(Quasar, { plugins: {} });
  if (router) app.use(router);
  const vm = app.mount(host);
  apps.push({ app, host });
  return { vm, host };
}
async function dialog(component, props) {
  const { vm, host } = mount(component, { ...props, modelValue: false });
  vm.$.props.modelValue = true;
  await nextTick();
  await nextTick();
  return { vm, host };
}
afterEach(() => {
  for (const { app, host } of apps.splice(0)) {
    app.unmount();
    host.remove();
  }
  document.body.innerHTML = '';
  vi.clearAllMocks();
});
describe('Componentes de seguimiento', () => {
  it('distingue estados validados y pendientes', async () => {
    const { host } = mount(StatusBadge, { value: 'validada' });
    expect(host.textContent).toContain('Validada');
    expect(host.querySelector('.status-badge').classList.contains('success')).toBe(true);
  });
  it('edita solo campos autorizados y conserva la revisión', async () => {
    api.mockResolvedValue({ id: 'doc', revision: 4 });
    await dialog(RecordForm, {
      resource: 'documents',
      schema: {
        label: 'Documentos',
        fields: [
          { key: 'title', label: 'Asunto', type: 'text', required: true },
          { key: 'date', label: 'Fecha', type: 'date', required: true },
        ],
      },
      record: {
        id: 'doc',
        title: 'Asunto anterior',
        date: '2026-10-13',
        status: 'aprobado',
        revision: 3,
      },
      preset: {},
      lookups: {},
    });
    const title = document.querySelector('input[type=text]');
    title.value = 'Asunto actualizado';
    title.dispatchEvent(new Event('input', { bubbles: true }));
    await nextTick();
    document
      .querySelector('form')
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    await vi.waitFor(() => expect(api).toHaveBeenCalled());
    expect(api.mock.calls[0]).toEqual([
      '/documents/doc',
      { method: 'PATCH', body: { title: 'Asunto actualizado', date: '2026-10-13', revision: 3 } },
    ]);
  });
  it('registra el envío mediante una acción sin aprobar el documento', async () => {
    api.mockResolvedValue({
      id: 'doc',
      preparation_status: 'remitido',
      approval_status: 'pendiente',
    });
    await dialog(ActionForm, {
      resource: 'documents',
      action: 'send',
      record: { id: 'doc', revision: 2 },
      lookups: {},
    });
    expect(document.body.textContent).toContain('La aprobación seguirá pendiente');
    document
      .querySelector('form')
      .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    await vi.waitFor(() => expect(api).toHaveBeenCalled());
    expect(api.mock.calls[0]).toEqual([
      '/documents/doc/send',
      { method: 'POST', body: { revision: 2 } },
    ]);
  });
  it('el cronograma calcula la barra con las fechas reales de cada actividad', () => {
    const { host } = mount(GanttChart, {
      tasks: [
        {
          id: 't',
          title: 'Actividad ficticia',
          start_date: '2026-10-01',
          due_date: '2026-10-10',
          progress: 50,
          status: 'en_progreso',
          _labels: { responsible_id: 'Responsable demo' },
        },
      ],
    });
    expect(host.textContent).toContain('Actividad ficticia');
    expect(host.querySelector('.gantt-bar').style.width).toBe('100%');
    expect(host.querySelector('.gantt-bar>span').style.width).toBe('50%');
  });
  it('abre el documento único vinculado desde la ficha de una tarea', async () => {
    const link = fixture['task-documents'].items[0];
    const task = fixture.tasks.items.find((t) => t.id === link.task_id);
    api.mockImplementation((path) =>
      Promise.resolve(
        path.startsWith('/task-documents?') ? { items: [link], total: 1 } : { items: [], total: 0 },
      ),
    );
    const router = createRouter({
      history: createMemoryHistory(),
      routes: ['/tareas', '/registro'].map((path) => ({ path, component: { template: '<div/>' } })),
    });
    await router.push('/tareas');
    await router.isReady();
    mount(
      RecordDetail,
      { modelValue: true, resource: 'tasks', record: task, meta: fixture.meta },
      router,
    );
    await vi.waitFor(() => expect(document.querySelector('.related-item')).not.toBeNull());
    const section = [...document.querySelectorAll('.related-section')].find((s) =>
      s.querySelector('h3').textContent.includes('Documentos de tareas'),
    );
    section.querySelector('.related-item').click();
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/registro'));
    expect(router.currentRoute.value.query.id).toBe(link.document_id);
  });
  it('abre la evidencia vinculada desde una tarea para consultar su validación', async () => {
    const task = fixture.tasks.items[0];
    const link = {
      id: 'link-demo',
      evidence_id: 'evidence-demo',
      task_id: task.id,
      _labels: { evidence_id: 'Evidencia demo' },
    };
    api.mockImplementation((path) =>
      Promise.resolve(
        path.startsWith('/evidence-links?') ? { items: [link], total: 1 } : { items: [], total: 0 },
      ),
    );
    const router = createRouter({
      history: createMemoryHistory(),
      routes: ['/tareas', '/evidencias'].map((path) => ({
        path,
        component: { template: '<div/>' },
      })),
    });
    await router.push('/tareas');
    await router.isReady();
    mount(
      RecordDetail,
      { modelValue: true, resource: 'tasks', record: task, meta: fixture.meta },
      router,
    );
    await vi.waitFor(() => expect(document.querySelector('.related-item')).not.toBeNull());
    const section = [...document.querySelectorAll('.related-section')].find((s) =>
      s.querySelector('h3').textContent.includes('Vínculos de evidencia'),
    );
    section.querySelector('.related-item').click();
    await vi.waitFor(() => expect(router.currentRoute.value.path).toBe('/evidencias'));
    expect(router.currentRoute.value.query.id).toBe('evidence-demo');
  });
  it('el dashboard representa los contadores entregados por la API', async () => {
    api.mockImplementation((path) =>
      Promise.resolve(
        path === '/lookups'
          ? { axes: [], users: [] }
          : {
              pending: 17,
              overdue: 3,
              upcoming: 2,
              pending_documents: 8,
              pending_agreements: 4,
              progress: 62,
              closed: 5,
              task_count: 22,
              projects: [],
              by_person: [],
              by_axis: [],
              upcoming_tasks: [],
              overdue_tasks: [],
            },
      ),
    );
    const router = createRouter({
      history: createMemoryHistory(),
      routes: ['/', '/proyectos', '/reportes', '/reuniones'].map((path) => ({
        path,
        component: { template: '<div/>' },
      })),
    });
    await router.push('/');
    await router.isReady();
    const DashboardInLayout = {
      render: () => h(QLayout, {}, () => h(QPageContainer, {}, () => h(DashboardView))),
    };
    const { host } = mount(DashboardInLayout, {}, router);
    await vi.waitFor(() => expect(host.querySelectorAll('.metric-card')).toHaveLength(4));
    const values = [...host.querySelectorAll('.metric-card strong')].map((e) => e.textContent);
    expect(values).toEqual(['17', '03', '02', '08']);
    expect(host.querySelector('.progress-ring').textContent).toContain('62');
  });
});
