import { createApp, nextTick } from 'vue';
import { Quasar } from 'quasar';
import { afterEach, expect, it, vi } from 'vitest';
import RecordForm from '../components/RecordForm.vue';
import ActionForm from '../components/ActionForm.vue';
import TaskProgress from '../components/TaskProgress.vue';
import ParticipantDirectory from '../components/ParticipantDirectory.vue';
import TaskDetail from '../components/TaskDetail.vue';
import TaskEvidenceForm from '../components/TaskEvidenceForm.vue';
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
it('asigna una tarea a varias personas con un solo selector y sin clasificación interna', async () => {
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
    preset: {
      title: 'Tarea compartida demo',
      responsible_id: 'member',
      member_ids: ['member', 'chief'],
      due_date: '2026-10-20',
    },
    lookups: {
      'task-members': workers,
      'task-themes': [{ value: 'theme', label: 'Temática de prueba' }],
    },
  });
  expect(document.querySelectorAll('.task-assignment-form .form-grid .q-field')).toHaveLength(4);
  for (const label of [
    'Proyecto',
    'Prioridad',
    'Recurrencia',
    'Tarea principal',
    'Temática',
    'Oficina',
    'participantes',
    'todo el equipo',
  ])
    expect(document.body.textContent).not.toContain(label);
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
        title: 'Tarea compartida demo',
        responsible_id: 'member',
        member_ids: ['chief'],
        due_date: '2026-10-20',
      },
    },
  ]);
});
it('edita una tarea sin sobrescribir su clasificación, oficina ni participantes anteriores', async () => {
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
    e.closest('.q-field').textContent.includes('¿Qué debe hacer?'),
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
        due_date: '2026-10-20',
        description: 'Instrucción anterior',
        revision: 3,
      },
    },
  ]);
});
it('adjunta una evidencia desde la tarea y usa el avance propio del responsable', async () => {
  session.user = { id: 'member' };
  api.mockResolvedValue({ id: 'task' });
  await dialog(ActionForm, {
    resource: 'tasks',
    action: 'advance',
    record: {
      id: 'task',
      title: 'Preparar informe',
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
  expect(document.body.textContent).not.toContain('Nombre de la evidencia');
  expect(document.querySelector('.q-select')).toBeNull();
  set('Enlace de la evidencia', 'https://drive.google.com/file/d/ficticio/view');
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
it('la ficha del responsable muestra las instrucciones y permite adjuntar evidencia sin campos internos', async () => {
  api.mockResolvedValue({ items: [], total: 0 });
  await dialog(TaskDetail, {
    record: {
      id: 'task',
      title: 'Preparar informe',
      due_date: '2026-10-20',
      status: 'pendiente',
      description: 'Revisar los resultados',
      can_advance: true,
      can_edit: false,
      project_id: 'proyecto-interno',
      priority: 'alta',
      recurrence: 'mensual',
      office: 'Oficina anterior',
      revision: 8,
      legacy_progress: 90,
      participants: [{ id: 'member', name: 'Integrante demo' }],
      _labels: { responsible_id: 'Integrante demo', created_by: 'Jefe demo' },
    },
  });
  await vi.waitFor(() => expect(document.body.textContent).toContain('Revisar los resultados'));
  const detail = document.querySelector('.task-detail');
  for (const value of [
    'proyecto-interno',
    'Oficina anterior',
    'Recurrencia',
    'Prioridad',
    'Revisión 8',
    'Agregar participantes',
  ])
    expect(detail.textContent).not.toContain(value);
  expect(detail.textContent).toContain('Integrante demo');
  expect(detail.textContent).toContain('Jefe demo');
  expect(detail.querySelector('textarea')).toBeNull();
  [...detail.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Añadir mi evidencia'))
    .click();
  await nextTick();
  expect(detail.querySelector('textarea')).not.toBeNull();
  expect(detail.textContent).toContain('Añadir mi evidencia');
  expect(detail.textContent).toContain('Enviar evidencia a revisión');
  expect(detail.textContent).not.toContain('Editar tarea');
});
it('un integrante adicional guarda su evidencia directamente sin editar la tarea', async () => {
  session.user = { id: 'member' };
  api.mockResolvedValue({ id: 'task', revision: 9 });
  const saved = vi.fn();
  const { host } = mount(TaskEvidenceForm, {
    record: {
      id: 'task',
      revision: 8,
      participants: [
        { id: 'chief', reported_progress: 90 },
        { id: 'member', reported_progress: 25 },
      ],
    },
    onSaved: saved,
  });
  [...host.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Enlace Drive/Docs'))
    .click();
  await nextTick();
  expect(host.querySelector('input[type=number]').value).toBe('25');
  const comment = host.querySelector('textarea');
  comment.value = 'Estoy preparando mi parte del informe';
  comment.dispatchEvent(new Event('input', { bubbles: true }));
  const link = host.querySelector('input[type=text]');
  link.value = 'https://drive.google.com/file/d/evidencia-miembro/view';
  link.dispatchEvent(new Event('input', { bubbles: true }));
  host.querySelector('.q-checkbox').click();
  await nextTick();
  host
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(saved).toHaveBeenCalledOnce());
  await nextTick();
  expect(host.querySelector('.q-field--error')).toBeNull();
  expect(api).toHaveBeenCalledWith('/tasks/task/advance', {
    method: 'POST',
    body: {
      revision: 8,
      progress: 25,
      comment: 'Estoy preparando mi parte del informe',
      evidence: {
        url: 'https://drive.google.com/file/d/evidencia-miembro/view',
        access_confirmed: true,
      },
    },
  });
});
it('al enviar cambia al historial aunque el servidor reemplace la tarea actualizada', async () => {
  session.user = { id: 'member' };
  const record = {
    id: 'task',
    revision: 1,
    can_advance: true,
    participants: [{ id: 'member', name: 'Integrante', reported_progress: 0 }],
  };
  const updated = { ...record, revision: 2, evidence_count: 1 };
  api.mockImplementation((path) =>
    Promise.resolve(
      path.startsWith('/task-updates?')
        ? {
            items: [
              {
                id: 'report',
                kind: 'avance',
                progress: 30,
                comment: 'Mi entrega',
                review_status: 'pendiente',
                can_review: false,
              },
            ],
            total: 1,
          }
        : updated,
    ),
  );
  let mounted;
  mounted = await dialog(TaskDetail, {
    record,
    initialTab: 'submit',
    onSaved: (value) => {
      mounted.vm.$.props.record = value;
    },
  });
  const detail = document.querySelector('.task-detail');
  [...detail.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Enlace Drive/Docs'))
    .click();
  await nextTick();
  const description = detail.querySelector('textarea');
  description.value = 'Mi entrega';
  description.dispatchEvent(new Event('input', { bubbles: true }));
  const link = detail.querySelector('input[type=text]');
  link.value = 'https://drive.google.com/file/d/entrega/view';
  link.dispatchEvent(new Event('input', { bubbles: true }));
  detail.querySelector('.q-checkbox').click();
  await nextTick();
  detail
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() =>
    expect(detail.textContent).toContain('Pendiente de revisión por jefatura'),
  );
  expect(detail.querySelector('textarea')).toBeNull();
  expect(detail.querySelector('.progress-entry').textContent).toContain('Mi entrega');
  expect(detail.textContent).not.toContain('Revisar avance');
});
it('cierra una tarea completa usando su evidencia validada sin pedir otro formulario', async () => {
  api.mockImplementation((path) =>
    Promise.resolve(
      path.startsWith('/task-updates?')
        ? {
            items: [
              {
                id: 'report',
                kind: 'avance',
                progress: 100,
                review_status: 'validada',
                evidence_version_id: 'version-validada',
                comment: 'Informe completo',
              },
            ],
            total: 1,
          }
        : {},
    ),
  );
  const saved = vi.fn();
  const { host } = mount(TaskProgress, {
    record: {
      id: 'task',
      revision: 5,
      status: 'en_revision',
      all_complete: true,
      can_review: true,
      reported_progress: 100,
      validated_progress: 100,
      participants: [],
    },
    onSaved: saved,
  });
  await vi.waitFor(() => expect(host.textContent).toContain('Cerrar tarea'));
  [...host.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Cerrar tarea'))
    .click();
  await nextTick();
  [...host.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Confirmar cierre'))
    .click();
  await vi.waitFor(() => expect(saved).toHaveBeenCalledOnce());
  expect(api).toHaveBeenCalledWith('/tasks/task/close', {
    method: 'POST',
    body: { revision: 5, evidence_version_id: 'version-validada' },
  });
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
