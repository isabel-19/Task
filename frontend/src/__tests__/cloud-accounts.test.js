import { createApp, h, nextTick } from 'vue';
import { Quasar, QLayout, QPageContainer } from 'quasar';
import { createMemoryHistory, createRouter } from 'vue-router';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import TaskEvidenceForm from '../components/TaskEvidenceForm.vue';
import CloudFilePicker from '../components/CloudFilePicker.vue';
import CloudAccountsView from '../views/CloudAccountsView.vue';
vi.mock('../api', async (original) => ({ ...(await original()), api: vi.fn() }));
vi.mock('../googlePicker', () => ({ selectGoogleFile: vi.fn() }));
import { api, session } from '../api';
import { selectGoogleFile } from '../googlePicker';
const apps = [];
beforeEach(() => {
  session.permissions = ['tasks.read', 'tasks.write'];
});
async function mount(component, props = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/cuentas', component: { render: () => null } },
      { path: '/tareas', component: { render: () => null } },
    ],
  });
  await router.push('/cuentas');
  await router.isReady();
  const host = document.createElement('div');
  document.body.append(host);
  const root =
    component === CloudAccountsView
      ? { render: () => h(QLayout, {}, () => h(QPageContainer, {}, () => h(component, props))) }
      : { render: () => h(component, props) };
  const app = createApp(root).use(Quasar).use(router);
  app.mount(host);
  apps.push({ app, host });
  return host;
}
afterEach(() => {
  for (const { app, host } of apps.splice(0)) {
    app.unmount();
    host.remove();
  }
  document.body.innerHTML = '';
  vi.resetAllMocks();
  session.user = null;
  session.permissions = [];
});
const accounts = [
  {
    provider: 'google',
    configured: true,
    connected: true,
    account_label: 'google@example.invalid',
  },
  {
    provider: 'microsoft',
    configured: true,
    connected: true,
    account_label: 'outlook@example.invalid',
  },
];
const button = (host, label) =>
  [...host.querySelectorAll('button')].find((item) => item.textContent.trim().includes(label));
it('explora y previsualiza el Drive de la persona vinculada sin exigir una tarea', async () => {
  api.mockImplementation((path) =>
    Promise.resolve(
      path === '/cloud/accounts'
        ? { items: accounts }
        : path === '/cloud/google/picker'
          ? { access_token: 'ephemeral-fixture', api_key: 'picker-key', app_id: '123' }
          : {
              type: 'application/json',
              text: async () =>
                JSON.stringify({ kind: 'text', text: 'Informe compartido por otra persona' }),
            },
    ),
  );
  selectGoogleFile.mockResolvedValue({
    provider: 'google',
    id: 'shared-doc',
    name: 'Documento compartido',
  });
  const host = await mount(CloudAccountsView);
  await vi.waitFor(() => expect(button(host, 'Explorar y previsualizar')).toBeDefined());
  button(host, 'Explorar y previsualizar').click();
  await vi.waitFor(() =>
    expect(document.querySelector('.evidence-text-preview')?.textContent).toContain(
      'Informe compartido por otra persona',
    ),
  );
  expect(api.mock.calls.some(([path]) => path.includes('/tasks/'))).toBe(false);
  expect(api).toHaveBeenCalledWith(
    '/cloud/google/preview',
    expect.objectContaining({ body: { item_id: 'shared-doc' } }),
  );
});
it('no ofrece habilitación general ni conexión a un usuario con permiso de consulta', async () => {
  session.permissions = ['tasks.read'];
  api.mockResolvedValue({ items: accounts.map((row) => ({ ...row, connected: false })) });
  const host = await mount(CloudAccountsView);
  await vi.waitFor(() => expect(host.querySelectorAll('.cloud-account-card')).toHaveLength(2));
  expect(button(host, 'Conectar cuenta')).toBeUndefined();
  expect(host.textContent).not.toContain('Habilitar conexiones para todos los usuarios');
  expect(api.mock.calls.some(([path]) => path === '/cloud/configuration')).toBe(false);
});
it('jefatura configura una vez y conserva los secretos guardados sin mostrarlos', async () => {
  session.permissions = ['tasks.read', 'tasks.write', 'admin.write'];
  const config = {
    revision: 3,
    encryption_ready: true,
    fields: {
      cloud_public_api_url: 'https://agenda.example.invalid/api',
      cloud_frontend_url: 'https://agenda.example.invalid',
      google_client_id: 'central-client',
      google_project_number: '123',
      microsoft_client_id: '',
      microsoft_tenant: 'common',
    },
    saved_secrets: {
      google_client_secret: true,
      google_picker_api_key: true,
      microsoft_client_secret: false,
    },
    providers: { google: { configured: true }, microsoft: { configured: false } },
  };
  api.mockImplementation((path, options) =>
    Promise.resolve(
      path === '/cloud/configuration'
        ? { ...config, revision: options ? 4 : 3 }
        : { items: accounts },
    ),
  );
  const host = await mount(CloudAccountsView);
  await vi.waitFor(() =>
    expect(host.textContent).toContain('Habilitar conexiones para todos los usuarios'),
  );
  host.querySelector('.q-expansion-item__container > .q-item').click();
  await vi.waitFor(() => expect(host.querySelector('.cloud-configuration-form')).not.toBeNull());
  const inputs = [...host.querySelectorAll('input[type=password]')];
  expect(inputs).toHaveLength(3);
  expect(inputs.every((input) => input.value === '')).toBe(true);
  expect(host.textContent).toContain('Credencial guardada. Deja vacío para conservarla.');
  host
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() =>
    expect(
      api.mock.calls.some(
        ([path, options]) => path === '/cloud/configuration' && options?.method === 'POST',
      ),
    ).toBe(true),
  );
  const [, options] = api.mock.calls.find(
    ([path, options]) => path === '/cloud/configuration' && options?.method === 'POST',
  );
  expect(options.body.revision).toBe(3);
  expect(options.body).not.toHaveProperty('google_client_secret');
  await vi.waitFor(() => expect(host.textContent).toContain('Configuración guardada'));
});
it('muestra claramente la habilitación pendiente sin fingir conexiones reales', async () => {
  api.mockResolvedValue({
    items: accounts.map((row) => ({ ...row, configured: false, connected: false })),
  });
  const host = await mount(CloudAccountsView);
  await vi.waitFor(() => expect(host.querySelectorAll('.cloud-account-card')).toHaveLength(2));
  expect(host.textContent).toContain('pendiente de habilitación por administración');
  expect(button(host, 'Conectar cuenta')).toBeUndefined();
  expect(host.textContent).toContain(
    'Los adjuntos recibidos por Outlook deben guardarse primero en OneDrive',
  );
});
it('conserva la cuenta vinculada si se cancela la desvinculación y la elimina al confirmar', async () => {
  let connected = true;
  api.mockImplementation((path) =>
    Promise.resolve(
      path.endsWith('/disconnect')
        ? ((connected = false), { ok: true })
        : { items: [{ ...accounts[0], connected }] },
    ),
  );
  const host = await mount(CloudAccountsView);
  await vi.waitFor(() => expect(host.textContent).toContain('google@example.invalid'));
  button(host, 'Desvincular').click();
  await nextTick();
  await vi.waitFor(() => expect(document.querySelector('.q-dialog')).not.toBeNull());
  button(document, 'Cancelar').click();
  await nextTick();
  expect(api.mock.calls.some(([path]) => path.endsWith('/disconnect'))).toBe(false);
  button(host, 'Desvincular').click();
  await nextTick();
  await vi.waitFor(() => expect(button(document, 'Desvincular cuenta')).toBeDefined());
  button(document, 'Desvincular cuenta').click();
  await vi.waitFor(() =>
    expect(api).toHaveBeenCalledWith('/cloud/google/disconnect', { method: 'POST' }),
  );
});
it('presenta un fallo de conexión recuperable sin redirigir fuera de la aplicación', async () => {
  api.mockImplementation((path) =>
    path.endsWith('/connect')
      ? Promise.reject(new Error('No se pudo autorizar la cuenta'))
      : Promise.resolve({ items: [{ ...accounts[0], connected: false }] }),
  );
  const host = await mount(CloudAccountsView);
  await vi.waitFor(() => expect(button(host, 'Conectar cuenta')).toBeDefined());
  button(host, 'Conectar cuenta').click();
  await vi.waitFor(() =>
    expect(host.querySelector('[role=alert]')?.textContent).toContain('No se pudo autorizar'),
  );
});
it('elige un documento con Google Picker y envía su identificador, no credenciales', async () => {
  session.user = { id: 'member' };
  api.mockImplementation((path) =>
    Promise.resolve(
      path === '/cloud/accounts'
        ? { items: accounts }
        : path === '/cloud/google/picker'
          ? { access_token: 'short-lived-fixture', api_key: 'picker-key', app_id: '123' }
          : { id: 'task', revision: 2 },
    ),
  );
  selectGoogleFile.mockResolvedValue({
    provider: 'google',
    id: 'doc-1',
    name: 'Informe de Google',
  });
  const saved = vi.fn();
  const host = await mount(TaskEvidenceForm, {
    record: { id: 'task', revision: 1, participants: [] },
    onSaved: saved,
  });
  button(host, 'Google / Microsoft').click();
  await nextTick();
  await vi.waitFor(() => expect(button(host, 'Elegir en Google Drive')).toBeDefined());
  button(host, 'Elegir en Google Drive').click();
  await vi.waitFor(() => expect(host.textContent).toContain('Informe de Google'));
  const description = host.querySelector('textarea');
  description.value = 'Mi evidencia desde Google';
  description.dispatchEvent(new Event('input', { bubbles: true }));
  await nextTick();
  host
    .querySelector('form')
    .dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
  await vi.waitFor(() => expect(saved).toHaveBeenCalledOnce());
  expect(api).toHaveBeenCalledWith('/tasks/task/advance-cloud', {
    method: 'POST',
    body: {
      revision: 1,
      progress: 0,
      comment: 'Mi evidencia desde Google',
      provider: 'google',
      item_id: 'doc-1',
    },
  });
  expect(host.textContent).not.toContain('short-lived-fixture');
});
it('permite navegar carpetas de OneDrive, paginar y elegir un archivo', async () => {
  api.mockImplementation((path) => {
    if (path === '/cloud/accounts') return Promise.resolve({ items: accounts });
    if (path.includes('folder=folder-1'))
      return Promise.resolve({
        items: [{ id: 'file-2', name: 'Informe final.pdf', folder: false, supported: true }],
        next_cursor: null,
      });
    if (path.includes('cursor=page2'))
      return Promise.resolve({
        items: [{ id: 'file-3', name: 'Segundo.pdf', folder: false, supported: true }],
        next_cursor: null,
      });
    return Promise.resolve({
      items: [{ id: 'folder-1', name: 'Informes', folder: true, supported: true }],
      next_cursor: 'page2',
    });
  });
  const selected = vi.fn();
  const host = await mount(CloudFilePicker, { 'onUpdate:modelValue': selected });
  await vi.waitFor(() => expect(button(host, 'Elegir en OneDrive')).toBeDefined());
  button(host, 'Elegir en OneDrive').click();
  await vi.waitFor(() =>
    expect(document.querySelector('.cloud-browser-dialog')?.textContent).toContain('Informes'),
  );
  button(document, 'Cargar más archivos').click();
  await vi.waitFor(() =>
    expect(document.querySelector('.cloud-browser-dialog')?.textContent).toContain('Segundo.pdf'),
  );
  [...document.querySelectorAll('.cloud-browser-dialog .q-item')]
    .find((item) => item.textContent.includes('Informes'))
    .click();
  await vi.waitFor(() =>
    expect(document.querySelector('.cloud-browser-dialog')?.textContent).toContain(
      'Informe final.pdf',
    ),
  );
  document.querySelector('.cloud-browser-dialog .q-item').click();
  await vi.waitFor(() =>
    expect(selected).toHaveBeenCalledWith({
      provider: 'microsoft',
      id: 'file-2',
      name: 'Informe final.pdf',
    }),
  );
});
it('al cancelar Google Picker conserva la entrega sin seleccionar un documento', async () => {
  api.mockResolvedValue({ items: accounts });
  selectGoogleFile.mockResolvedValue(null);
  const selected = vi.fn();
  const host = await mount(CloudFilePicker, { 'onUpdate:modelValue': selected });
  await vi.waitFor(() => expect(button(host, 'Elegir en Google Drive')).toBeDefined());
  button(host, 'Elegir en Google Drive').click();
  await vi.waitFor(() => expect(selectGoogleFile).toHaveBeenCalled());
  expect(selected).not.toHaveBeenCalled();
});
