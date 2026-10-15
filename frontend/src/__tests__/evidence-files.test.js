import { createApp, nextTick } from 'vue';
import { Quasar } from 'quasar';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import TaskEvidenceForm from '../components/TaskEvidenceForm.vue';
import EvidencePreview from '../components/EvidencePreview.vue';
vi.mock('../api', async (original) => ({ ...(await original()), api: vi.fn() }));
import { api, session } from '../api';
const apps = [];
function mount(component, props) {
  const host = document.createElement('div');
  document.body.append(host);
  const app = createApp(component, props).use(Quasar);
  const vm = app.mount(host);
  apps.push({ app, host });
  return { host, vm };
}
beforeEach(() => {
  api.mockReset();
  session.user = { id: 'member' };
});
afterEach(() => {
  for (const { app, host } of apps.splice(0)) {
    app.unmount();
    host.remove();
  }
  document.body.innerHTML = '';
  vi.restoreAllMocks();
  session.user = null;
});
const record = { id: 'task', revision: 3, participants: [{ id: 'member', reported_progress: 40 }] };
it('adjunta un archivo del equipo sin exigir enlace ni confirmación de Drive', async () => {
  api.mockResolvedValue({ id: 'task', revision: 4 });
  const saved = vi.fn();
  const { host } = mount(TaskEvidenceForm, { record, onSaved: saved });
  expect(host.textContent).toContain('Archivo de mi equipo');
  expect(host.querySelector('.q-checkbox')).toBeNull();
  const description = host.querySelector('textarea');
  description.value = 'Informe adjunto del equipo';
  description.dispatchEvent(new Event('input', { bubbles: true }));
  const file = new File(['Mi evidencia local'], 'informe.txt', { type: 'text/plain' });
  const input = host.querySelector('input[type=file]');
  Object.defineProperty(input, 'files', { value: [file] });
  input.dispatchEvent(new Event('change', { bubbles: true }));
  await nextTick();
  host
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(saved).toHaveBeenCalledOnce());
  const [path, options] = api.mock.calls[0];
  expect(path).toBe('/tasks/task/advance-file');
  expect(options.body).toBeInstanceOf(FormData);
  expect(options.body.get('file').name).toBe('informe.txt');
  expect(options.body.get('comment')).toBe('Informe adjunto del equipo');
  expect(options.body.get('progress')).toBe('40');
  expect(options.body.get('revision')).toBe('3');
  expect(options.body.has('evidence')).toBe(false);
});
it('informa cuando el archivo supera el límite y evita enviarlo', async () => {
  const { host } = mount(TaskEvidenceForm, {
    record,
    uploadOptions: { max_bytes: 5, extensions: ['.txt'] },
  });
  const input = host.querySelector('input[type=file]');
  Object.defineProperty(input, 'files', { value: [new File(['mucho contenido'], 'informe.txt')] });
  input.dispatchEvent(new Event('change', { bubbles: true }));
  await nextTick();
  expect(host.querySelector('[role=alert]').textContent).toContain('supera');
  expect(api).not.toHaveBeenCalled();
});
it('permite usar enlaces cuando la instalación tiene deshabilitada la carga de archivos', async () => {
  const { host } = mount(TaskEvidenceForm, { record, uploadOptions: { enabled: false } });
  await nextTick();
  expect(host.querySelector('input[type=file]')).toBeNull();
  expect(host.textContent).toContain('Enlace de mi evidencia');
  expect(host.querySelector('.q-checkbox')).not.toBeNull();
  const fileOption = [...host.querySelectorAll('button')].find((button) =>
    button.textContent.includes('Archivo de mi equipo'),
  );
  expect(fileOption.disabled).toBe(true);
});
async function openPreview(file) {
  const mounted = mount(EvidencePreview, { modelValue: false, file });
  mounted.vm.$.props.modelValue = true;
  await nextTick();
  await nextTick();
  return mounted;
}
it('previsualiza un documento compartido de Google sin presentar ni guardar una evidencia', async () => {
  api.mockResolvedValue({
    type: 'application/json',
    text: async () => JSON.stringify({ kind: 'text', text: '<b>Compartido conmigo</b>' }),
  });
  await openPreview({
    id: 'shared-1',
    name: 'Informe compartido',
    cloud: { item_id: 'shared-1' },
    url: 'https://drive.google.com/file/d/shared-1/view',
  });
  await vi.waitFor(() =>
    expect(document.querySelector('.evidence-text-preview')?.textContent).toContain(
      'Compartido conmigo',
    ),
  );
  expect(api).toHaveBeenCalledOnce();
  expect(api).toHaveBeenCalledWith(
    '/cloud/google/preview',
    expect.objectContaining({
      method: 'POST',
      body: { item_id: 'shared-1' },
      responseType: 'blob',
    }),
  );
  expect(document.querySelector('.evidence-text-preview b')).toBeNull();
  expect(document.body.textContent).toContain('Todavía no se ha presentado como evidencia');
  expect(
    document.querySelector('a[href="https://drive.google.com/file/d/shared-1/view"]')?.textContent,
  ).toContain('Abrir en Google');
  expect(document.querySelector('a[href$="?download=true"]')).toBeNull();
});
it('conserva la opción de abrir en Google cuando el propietario impide copiar el archivo', async () => {
  api.mockRejectedValue(new Error('El propietario no permite descargar o copiar este documento.'));
  await openPreview({
    id: 'restricted',
    name: 'Documento restringido',
    cloud: { item_id: 'restricted' },
    url: 'https://drive.google.com/file/d/restricted/view',
  });
  await vi.waitFor(() =>
    expect(document.querySelector('[role=alert]')?.textContent).toContain('propietario'),
  );
  expect(
    document.querySelector('a[href="https://drive.google.com/file/d/restricted/view"]'),
  ).not.toBeNull();
});
it('muestra el contenido de Word como texto y no interpreta etiquetas HTML', async () => {
  api.mockResolvedValue({
    kind: 'text',
    text: '<script>no ejecutar</script> Informe del equipo',
    truncated: false,
  });
  await openPreview({
    id: 'file',
    name: 'informe.docx',
    url: '/api/evidence-files/file',
    content_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  });
  await vi.waitFor(() =>
    expect(document.querySelector('.evidence-text-preview')?.textContent).toContain('<script>'),
  );
  expect(document.querySelector('.evidence-text-preview script')).toBeNull();
  expect(api).toHaveBeenCalledWith('/evidence-files/file/preview', expect.any(Object));
  expect(document.querySelector('a[href$="?download=true"]')).not.toBeNull();
});
it('presenta hojas y celdas de Excel y avisa cuando la vista está limitada', async () => {
  api.mockResolvedValue({
    kind: 'table',
    sheets: [
      {
        name: 'Hoja 1',
        rows: [
          ['Persona', 'Avance'],
          ['Elena', '60'],
        ],
      },
    ],
    truncated: true,
  });
  await openPreview({
    id: 'file',
    name: 'avance.xlsx',
    url: '/api/evidence-files/file',
    content_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  await vi.waitFor(() =>
    expect(document.querySelectorAll('.evidence-table-scroll td')).toHaveLength(4),
  );
  expect(document.body.textContent).toContain('Elena');
  expect(document.body.textContent).toContain('archivo original se conserva completo');
});
it('permite reintentar la vista previa y descargar el original si falla', async () => {
  api
    .mockRejectedValueOnce(new Error('Archivo no disponible'))
    .mockResolvedValueOnce({ kind: 'text', text: 'Contenido recuperado' });
  await openPreview({
    id: 'file',
    name: 'informe.txt',
    url: '/api/evidence-files/file',
    content_type: 'text/plain',
  });
  await vi.waitFor(() =>
    expect(document.querySelector('[role=alert]')?.textContent).toContain('Archivo no disponible'),
  );
  [...document.querySelectorAll('button')]
    .find((button) => button.textContent.includes('Reintentar'))
    .click();
  await vi.waitFor(() =>
    expect(document.querySelector('.evidence-text-preview')?.textContent).toBe(
      'Contenido recuperado',
    ),
  );
});
