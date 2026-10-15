import { createApp, nextTick } from 'vue';
import { Quasar } from 'quasar';
import { afterEach, expect, it, vi } from 'vitest';
import { dayKey, weekStart, weekDays, shiftDay } from '../taskAgenda';
import TaskAgenda from '../components/TaskAgenda.vue';
import EntityTable from '../components/EntityTable.vue';
import StatusBadge from '../components/StatusBadge.vue';
import TaskAssigner from '../components/TaskAssigner.vue';
const apps = [];
function mount(component, props) {
  const host = document.createElement('div');
  document.body.append(host);
  const app = createApp(component, props).use(Quasar);
  app.mount(host);
  apps.push({ app, host });
  return host;
}
afterEach(() => {
  for (const { app, host } of apps.splice(0)) {
    app.unmount();
    host.remove();
  }
});
const row = {
  id: 'task',
  title: 'Revisar informe',
  due_date: '2026-10-14',
  status: 'en_progreso',
  participants: [{ name: 'Integrante' }],
  can_advance: true,
  evidence_count: 2,
  latest_evidence_url: 'https://drive.google.com/file/d/ficticio/view',
  _labels: { created_by: 'Jefatura de prueba' },
};
it('calcula semanas locales al cruzar meses y años, incluido el domingo', () => {
  expect(dayKey(weekStart(new Date(2027, 0, 3)))).toBe('2026-12-28');
  expect(weekDays(weekStart(new Date(2027, 0, 3))).map((day) => day.key)).toEqual([
    '2026-12-28',
    '2026-12-29',
    '2026-12-30',
    '2026-12-31',
    '2027-01-01',
    '2027-01-02',
    '2027-01-03',
  ]);
  expect(dayKey(shiftDay(weekStart(new Date(2027, 0, 3)), 7))).toBe('2027-01-04');
});
it('ubica la tarea en su fecha y permite abrir documento, historial y envío por separado', async () => {
  const evidence = vi.fn(),
    submit = vi.fn();
  const host = mount(TaskAgenda, {
    rows: [row],
    start: weekStart(new Date(2026, 9, 14)),
    pagination: { page: 1, rowsPerPage: 100, rowsNumber: 1 },
    onEvidence: evidence,
    onSubmit: submit,
  });
  expect(host.querySelectorAll('.agenda-day')).toHaveLength(7);
  expect(host.querySelector('.task-assigner').textContent).toContain('Jefatura de prueba');
  expect(
    host.querySelector('.agenda-task').closest('.agenda-day').querySelector('h3').textContent,
  ).toContain('14');
  const link = host.querySelector('a');
  expect(link.href).toBe(row.latest_evidence_url);
  expect(link.textContent).toContain('Abrir documento');
  expect(link.target).toBe('_blank');
  expect(link.rel).toBe('noopener noreferrer');
  [...host.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Ver evidencias'))
    .click();
  [...host.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Añadir evidencia'))
    .click();
  await nextTick();
  expect(evidence).toHaveBeenCalledWith(row);
  expect(submit).toHaveBeenCalledWith(row);
});
it('abre el documento directamente desde el listado sin abrir el detalle de la tarea', async () => {
  const open = vi.fn(),
    evidence = vi.fn();
  const host = mount(EntityTable, {
    resource: 'tasks',
    schema: { fields: [] },
    rows: [row],
    pagination: { page: 1, rowsPerPage: 20, rowsNumber: 1 },
    onOpen: open,
    onEvidence: evidence,
  });
  const link = host.querySelector('a');
  expect(host.querySelector('.task-assigner').textContent).toContain(
    'Asignada por: Jefatura de prueba',
  );
  expect(link.href).toBe(row.latest_evidence_url);
  link.addEventListener('click', (event) => event.preventDefault());
  link.click();
  expect(open).not.toHaveBeenCalled();
  [...host.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Ver evidencias'))
    .click();
  await nextTick();
  expect(evidence).toHaveBeenCalledWith(row);
});
it('indica si no existe autor recuperable, sin atribuir la tarea al último editor', () => {
  const host = mount(TaskAssigner, {
    record: { modified_by: 'editor', _labels: { modified_by: 'Editor posterior' } },
  });
  expect(host.textContent).toContain('No registrado');
  expect(host.textContent).not.toContain('Editor posterior');
});
it.each([
  ['pendiente', 'danger'],
  ['en_progreso', 'warning'],
  ['en_revision', 'info'],
  ['cerrada', 'success'],
])('distingue el estado %s con color y texto', (value, color) => {
  const host = mount(StatusBadge, { value });
  expect(host.querySelector('.status-badge').classList.contains(color)).toBe(true);
  expect(host.textContent.trim().length).toBeGreaterThan(0);
});
