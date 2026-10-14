import { createApp, nextTick } from 'vue';
import { Quasar } from 'quasar';
import { afterEach, expect, it, vi } from 'vitest';
import RecordForm from '../components/RecordForm.vue';
import ActionForm from '../components/ActionForm.vue';
import TaskProgress from '../components/TaskProgress.vue';
import ParticipantDirectory from '../components/ParticipantDirectory.vue';
vi.mock('../api', async (original) => ({ ...(await original()), api: vi.fn() }));
import { api, session } from '../api';
const apps = [];
function mount(component, props) {
  const host = document.createElement('div');
  document.body.append(host);
  const app = createApp(component, props).use(Quasar, { plugins: {} });
  const vm = app.mount(host);
  apps.push({ app, host });
  return { vm, host };
}
async function dialog(component, props) {
  const mounted = mount(component, { ...props, modelValue: false });
  mounted.vm.$.props.modelValue = true;
  await nextTick();
  await nextTick();
  return mounted;
}
afterEach(() => {
  for (const { app, host } of apps.splice(0)) {
    app.unmount();
    host.remove();
  }
  document.body.innerHTML = '';
  vi.clearAllMocks();
  session.user = null;
});
const workers = [
  { value: 'chief', label: 'Jefe demo' },
  { value: 'member', label: 'Integrante demo' },
];
it('asigna una nueva tarea a todo el equipo en una sola petición', async () => {
  session.user = { id: 'chief' };
  api.mockResolvedValue({ id: 'task' });
  await dialog(RecordForm, {
    resource: 'tasks',
    schema: {
      label: 'Tareas',
      fields: [
        { key: 'title', type: 'text', label: 'Nombre', required: true },
        { key: 'responsible_id', lookup: 'users', label: 'Responsable', required: true },
      ],
    },
    record: null,
    preset: { title: 'Tarea grupal demo', due_date: '2026-10-20' },
    lookups: {
      'task-members': workers,
      'task-themes': [{ value: 'theme', label: 'Temática de prueba' }],
    },
  });
  expect(document.querySelectorAll('.task-assignment-form .form-grid .q-field')).toHaveLength(6);
  for (const label of ['Proyecto', 'Prioridad', 'Recurrencia', 'Tarea principal'])
    expect(document.body.textContent).not.toContain(label);
  [...document.querySelectorAll('button')]
    .find((b) => b.textContent.includes('Asignar a todo el equipo'))
    .click();
  await nextTick();
  document
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(api).toHaveBeenCalled());
  expect(api.mock.calls[0]).toEqual([
    '/tasks',
    {
      method: 'POST',
      body: {
        title: 'Tarea grupal demo',
        axis_id: 'theme',
        responsible_id: 'chief',
        due_date: '2026-10-20',
        office: null,
        member_ids: ['chief', 'member'],
      },
    },
  ]);
});
it('edita una actividad conservando los campos internos y usando las oficinas del Excel', async () => {
  api.mockResolvedValue({ id: 'task', revision: 4 });
  await dialog(RecordForm, {
    resource: 'tasks',
    schema: { label: 'Tareas', fields: [] },
    record: {
      id: 'task',
      title: 'Actividad anterior',
      axis_id: 'theme',
      responsible_id: 'chief',
      due_date: '2026-10-20',
      start_date: '2026-10-01',
      project_id: 'legacy',
      priority: 'alta',
      recurrence: 'mensual',
      revision: 3,
      office: 'Oficina de prueba',
      description: 'Instrucción anterior',
      member_ids: ['chief', 'member'],
    },
    preset: {},
    lookups: {
      'task-members': workers,
      'task-themes': [{ value: 'theme', label: 'Tema de prueba' }],
      offices: [{ value: 'Oficina de prueba', label: 'Oficina de prueba' }],
    },
  });
  const activity = [...document.querySelectorAll('textarea')].find((e) =>
    e.closest('.q-field').textContent.includes('Actividad / tarea'),
  );
  activity.value = 'Actividad actualizada';
  activity.dispatchEvent(new Event('input', { bubbles: true }));
  await nextTick();
  document
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(api).toHaveBeenCalled());
  expect(api.mock.calls[0]).toEqual([
    '/tasks/task',
    {
      method: 'PATCH',
      body: {
        title: 'Actividad actualizada',
        axis_id: 'theme',
        responsible_id: 'chief',
        due_date: '2026-10-20',
        office: 'Oficina de prueba',
        description: 'Instrucción anterior',
        revision: 3,
      },
    },
  ]);
});
it('envía mi porcentaje y la evidencia sin usar el porcentaje de otra persona', async () => {
  session.user = { id: 'member' };
  api.mockResolvedValue({ id: 'task' });
  await dialog(ActionForm, {
    resource: 'tasks',
    action: 'advance',
    record: {
      id: 'task',
      revision: 7,
      progress: 90,
      participants: [{ id: 'member', reported_progress: 30 }],
    },
    lookups: {},
  });
  const inputs = [...document.querySelectorAll('input')];
  expect(document.querySelector('input[type=number]').value).toBe('30');
  const set = (label, value) => {
    const el = inputs.find((i) => i.closest('.q-field').textContent.includes(label));
    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  };
  set('Nombre de la evidencia', 'Informe de prueba');
  set('Enlace de Google', 'https://drive.google.com/file/d/ficticio/view');
  const textarea = document.querySelector('textarea');
  textarea.value = 'Mi aporte de prueba';
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
  document.querySelector('.q-checkbox').click();
  await nextTick();
  document
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(api).toHaveBeenCalled());
  expect(api.mock.calls[0]).toEqual([
    '/tasks/task/advance',
    {
      method: 'POST',
      body: {
        revision: 7,
        progress: 30,
        kind: 'avance',
        comment: 'Mi aporte de prueba',
        evidence: {
          title: 'Informe de prueba',
          url: 'https://drive.google.com/file/d/ficticio/view',
          access_confirmed: true,
        },
      },
    },
  ]);
});
it('permite al jefe revisar un aporte y conserva la revisión de la tarea', async () => {
  const report = {
    id: 'report',
    progress: 60,
    kind: 'avance',
    comment: 'Aporte demo',
    review_status: 'pendiente',
    can_review: true,
    url: 'https://drive.google.com/file/d/ficticio/view',
    _labels: { author_id: 'Integrante demo' },
  };
  api.mockImplementation((path) =>
    Promise.resolve(path.startsWith('/task-updates?') ? { items: [report], total: 1 } : {}),
  );
  const saved = vi.fn();
  const { host } = mount(TaskProgress, {
    record: {
      id: 'task',
      revision: 9,
      can_review: true,
      reported_progress: 30,
      validated_progress: 0,
      participants: [
        {
          id: 'member',
          name: 'Integrante demo',
          reported_progress: 60,
          validated_progress: 0,
          review_status: 'pendiente',
        },
      ],
    },
    onSaved: saved,
  });
  await vi.waitFor(() => expect(host.textContent).toContain('Aporte demo'));
  expect(host.querySelector('a').rel).toBe('noopener noreferrer');
  [...host.querySelectorAll('button')]
    .find((b) => b.textContent.includes('Revisar avance'))
    .click();
  await nextTick();
  const textarea = host.querySelector('textarea');
  textarea.value = 'Contenido revisado por el jefe';
  textarea.dispatchEvent(new Event('input', { bubbles: true }));
  await nextTick();
  host
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(saved).toHaveBeenCalled());
  expect(api.mock.calls.find(([path]) => path.endsWith('/review'))).toEqual([
    '/task-updates/report/review',
    {
      method: 'POST',
      body: { revision: 9, status: 'validada', note: 'Contenido revisado por el jefe' },
    },
  ]);
});
it('muestra los aportes al integrante sin botones de validación', async () => {
  api.mockResolvedValue({
    items: [
      {
        id: 'report',
        kind: 'avance',
        progress: 40,
        review_status: 'pendiente',
        can_review: false,
        comment: 'Mi aporte',
        _labels: { author_id: 'Integrante demo' },
      },
    ],
    total: 1,
  });
  const { host } = mount(TaskProgress, {
    record: {
      id: 'task',
      revision: 1,
      can_review: false,
      reported_progress: 40,
      validated_progress: 0,
      participants: [],
    },
  });
  await vi.waitFor(() => expect(host.textContent).toContain('Mi aporte'));
  expect(host.textContent).not.toContain('Revisar avance');
  expect(api.mock.calls[0][0]).toContain('scope=personal');
});
it('muestra los participantes del Excel y asigna una tarea desde el directorio', async () => {
  session.permissions = ['tasks.read', 'tasks.write'];
  api.mockResolvedValue({
    imported_count: 1,
    items: [
      {
        id: 'imported',
        name: 'Participante de prueba',
        roles: ['integrante'],
        source: 'Excel ROADMAP',
        aliases: [],
        possible_variants: ['Nombre similar de prueba'],
        task_count: 0,
        local_access: true,
        identifier: 'prueba@participantes.invalid',
      },
    ],
  });
  const assigned = vi.fn();
  await dialog(ParticipantDirectory, { onAssign: assigned });
  await vi.waitFor(() => expect(document.body.textContent).toContain('Participante de prueba'));
  expect(document.body.textContent).toContain('1 nombres registrados desde el Excel');
  expect(document.body.textContent).toContain('Revisar posible variante');
  [...document.querySelectorAll('button')]
    .find((b) => b.textContent.includes('Asignar tarea'))
    .click();
  expect(assigned).toHaveBeenCalledWith('imported');
});
