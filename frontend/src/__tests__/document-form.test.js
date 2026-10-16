import { createApp, nextTick } from 'vue';
import { Quasar } from 'quasar';
import { describe, it, expect, vi, afterEach } from 'vitest';
import RecordForm from '../components/RecordForm.vue';
vi.mock('../api', async (original) => ({ ...(await original()), api: vi.fn() }));
import { api, session } from '../api';

const schema = { label: 'Documentos', fields: [
  { key: 'number', label: 'Número', type: 'text' },
  { key: 'document_type_id', label: 'Tipo documental', lookup: 'document-types', required: true },
  { key: 'section', label: 'Sección', options: ['emitidos', 'recibidos', 'normativos'], required: true },
  { key: 'year', label: 'Año', type: 'number', required: true },
  { key: 'axis_id', label: 'Eje temático', lookup: 'axes', nullable: true },
  { key: 'project_id', label: 'Proyecto', lookup: 'projects', nullable: true },
  { key: 'reference_id', label: 'Documento de referencia', lookup: 'documents', nullable: true },
  { key: 'title', label: 'Nombre / asunto', type: 'text', required: true },
  { key: 'date', label: 'Fecha', type: 'date', required: true },
  { key: 'sender', label: 'Emisor', type: 'text', required: true },
  { key: 'recipient', label: 'Destinatario', type: 'text', required: true },
  { key: 'responsible_id', label: 'Responsable OGC', lookup: 'users', required: true },
  { key: 'preparation_status', label: 'Estado de envío', type: 'text', default: 'por_inicio', options: ['por_inicio', 'en_redaccion', 'listo_para_envio', 'enviado_digital', 'enviado_fisico', 'enviado_fisico_y_digital', 'anulado'] },
  { key: 'sent_date', label: 'Fecha de envío', type: 'date', nullable: true },
  { key: 'due_date', label: 'Fecha límite de atención', type: 'date', nullable: true },
  { key: 'followup_frequency', label: 'Frecuencia de seguimiento', options: ['diaria', 'semanal', 'quincenal', 'no_es_necesario'], nullable: true },
  { key: 'intake_format', label: 'Formato de recepción', options: ['digital', 'fisico', 'ambos'], nullable: true },
  { key: 'url', label: 'Enlace del documento', type: 'text' },
  { key: 'access_confirmed', type: 'boolean' },
] };
let app, host;
async function open(record) {
  session.user = { id: 'admin', name: 'Administración ficticia' };
  host = document.createElement('div'); document.body.appendChild(host);
  app = createApp(RecordForm, { modelValue: false, resource: 'documents', schema, record, preset: {},
    lookups: { 'document-types': [{ value: 'carta', label: 'Carta' }], users: [{ value: 'admin', label: 'Administración' }],
      'document-recipients': [{ value: 'Rectorado', label: 'Rectorado' }, { value: 'DIGA', label: 'DIGA' }, { value: 'SUNEDU', label: 'SUNEDU' }],
      axes: [{ value: 'eje', label: 'Acreditación' }], projects: [{ value: 'legacy', label: 'Proyecto anterior' }],
    },
  }).use(Quasar);
  const vm = app.mount(host);
  vm.$.props.modelValue = true;
  await nextTick(); await nextTick();
}
function input(label) {
  const field = [...document.querySelectorAll('.q-field')].find((field) => field.querySelector('.q-field__label')?.textContent.startsWith(label));
  return field.querySelector('input, textarea');
}
async function fill(label, value) {
  const element = input(label); element.value = value;
  element.dispatchEvent(new Event('input', { bubbles: true })); await nextTick();
}
async function submit() {
  document.querySelector('form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
}
async function choose(label, value) {
  const field = [...document.querySelectorAll('.q-field')].find((field) => field.querySelector('.q-field__label')?.textContent.startsWith(label));
  field.querySelector('input').focus();
  field.querySelector('input').dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', keyCode: 40, bubbles: true, cancelable: true }));
  await vi.waitFor(() => {
    const options = [...document.querySelectorAll('[role=option]')];
    expect(options.some((option) => option.textContent.trim() === value), JSON.stringify({ label, options: options.map((option) => option.textContent), menu: document.querySelector('.q-menu')?.textContent })).toBe(true);
  });
  [...document.querySelectorAll('[role=option]')].find((option) => option.textContent.trim() === value).click();
  await nextTick();
}
afterEach(() => { app?.unmount(); document.body.innerHTML = ''; vi.clearAllMocks(); session.user = null; });

describe('Registro Digital desde un único formulario', () => {
  it('sugiere el correlativo y guarda el enlace sin enviar como definitivo el número mostrado', async () => {
    api.mockImplementation((path) => Promise.resolve(path.includes('next-number')
      ? { automatic: true, number: 'CARTA N° 501-2026-UNAJMA-OGC' } : { id: 'documento' }));
    await open();
    await vi.waitFor(() => expect(input('Número').value).toBe('CARTA N° 501-2026-UNAJMA-OGC'));
    expect(input('Número').readOnly).toBe(true);
    await fill('Asunto del documento', 'Solicitud ficticia');
    await choose('Destinatario', 'Rectorado');
    await choose('Eje temático', 'Acreditación');
    await fill('Enlace del documento', 'https://docs.google.com/document/d/prueba/edit');
    await submit();
    await vi.waitFor(() => expect(api.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(true));
    const [path, { body }] = api.mock.calls.find(([, options]) => options?.method === 'POST');
    expect(path).toBe('/documents');
    expect(body.automatic_number).toBe(true);
    expect(body.number).toBeUndefined();
    expect(body.url).toBe('https://docs.google.com/document/d/prueba/edit');
    expect(body.responsible_id).toBe('admin');
    expect(body.recipient).toBe('Rectorado');
    expect(body.axis_id).toBe('eje');
    expect(body.project_id).toBeUndefined();
    expect(body.sender).toBeUndefined();
    expect(document.body.textContent).not.toContain('Proyecto');
    expect(document.body.textContent).not.toContain('Emisor');
    expect(document.querySelector('.document-number-panel')).toBeNull();
    expect([...document.querySelectorAll('.q-field__label')].filter((label) => label.textContent.startsWith('Número'))).toHaveLength(1);
  });

  it('edita el enlace manteniendo el número y la revisión del documento', async () => {
    api.mockResolvedValue({ id: 'doc', revision: 4 });
    await open({ id: 'doc', revision: 3, number: 'CARTA N° 500-2026-UNAJMA-OGC', document_type_id: 'carta',
      section: 'emitidos', year: 2026, title: 'Solicitud ficticia', date: '2026-10-14', sender: 'OGC',
      recipient: 'Área ficticia', responsible_id: 'admin', project_id: 'legacy', axis_id: 'eje', url: 'https://docs.google.com/document/d/v1/edit', access_confirmed: true });
    expect(input('Enlace del documento').value).toContain('/v1/');
    await fill('Enlace del documento', 'https://www.unajma.edu.pe/documento-ficticio.pdf');
    await submit();
    await vi.waitFor(() => expect(api).toHaveBeenCalled());
    const [path, { body }] = api.mock.calls[0];
    expect(path).toBe('/documents/doc');
    expect(body.number).toBe('CARTA N° 500-2026-UNAJMA-OGC');
    expect(body.revision).toBe(3);
    expect(body.url).toBe('https://www.unajma.edu.pe/documento-ficticio.pdf');
    expect(body.automatic_number).toBeUndefined();
    expect(body.project_id).toBeUndefined();
  });

  it('ofrece abrir el enlace solo cuando ya es una fuente admitida', async () => {
    api.mockResolvedValue({ automatic: true, number: 'CARTA N° 502-2026-UNAJMA-OGC' });
    await open();
    await vi.waitFor(() => expect(input('Número').readOnly).toBe(true));
    const openLink = () => [...document.querySelectorAll('a')].find((a) => a.textContent.includes('Abrir enlace'));
    expect(openLink()).toBeUndefined();
    await fill('Enlace del documento', 'https://unajma.edu.pe.evil.invalid/documento');
    expect(openLink()).toBeUndefined();
    await fill('Enlace del documento', 'https://docs.google.com/document/d/ficticio/edit');
    await vi.waitFor(() => expect(openLink()?.getAttribute('href')).toBe('https://docs.google.com/document/d/ficticio/edit'));
    expect(openLink().getAttribute('target')).toBe('_blank');
    expect(openLink().getAttribute('rel')).toContain('noopener');
  });

  it('impide guardar un enlace ajeno a las fuentes institucionales admitidas', async () => {
    api.mockResolvedValue({ automatic: true, number: 'CARTA N° 501-2026-UNAJMA-OGC' });
    await open();
    await vi.waitFor(() => expect(input('Número').readOnly).toBe(true));
    await fill('Asunto del documento', 'Documento ficticio'); await choose('Destinatario', 'Rectorado');
    await fill('Enlace del documento', 'https://unajma.edu.pe.evil.invalid/documento');
    await submit();
    await vi.waitFor(() => expect(document.body.textContent).toContain('Usa un enlace HTTPS de Drive, Docs o UNAJMA.'));
    expect(api.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(false);
  });

  it('usa la lista de entidades también para el remitente de un documento recibido', async () => {
    api.mockResolvedValue({ id: 'recibido', revision: 2 });
    await open({ id: 'recibido', revision: 1, number: 'OFICIO EXTERNO 018-2026', document_type_id: 'carta',
      section: 'recibidos', year: 2026, title: 'Documento recibido', date: '2026-10-14', sender: 'SUNEDU',
      recipient: 'Rectorado', responsible_id: 'admin' });
    expect(input('Entidad remitente').value).toBe('SUNEDU');
    await choose('Unidad orgánica a la que se derivó', 'DIGA');
    await submit();
    await vi.waitFor(() => expect(api).toHaveBeenCalled());
    const [path, { body }] = api.mock.calls[0];
    expect(path).toBe('/documents/recibido');
    expect(body.recipient).toBe('DIGA');
    expect(body.sender).toBe('SUNEDU');
    expect(body.number).toBe('OFICIO EXTERNO 018-2026');
    expect(document.body.textContent).toContain('Responsable de atención OGC');
    expect(document.body.textContent).not.toContain('Remitente (personal OGC)');
  });
  it('guarda un envío físico con fecha real y no confunde el enlace con el medio de envío', async () => {
    api.mockImplementation((path) => Promise.resolve(path.includes('next-number')
      ? { automatic: true, number: 'CARTA N° 501-2026-UNAJMA-OGC' } : { id:'doc' }));
    await open();
    await vi.waitFor(() => expect(input('Número').value).toContain('501'));
    expect([...document.querySelectorAll('label')].some((label) => label.textContent.includes('Fecha de envío'))).toBe(false);
    await fill('Asunto del documento', 'Entrega física ficticia');
    await choose('Destinatario', 'Rectorado');
    await fill('Fecha del documento', '2026-10-12');
    await choose('Estado de envío', 'Enviado físico');
    await fill('Enlace del documento', 'https://drive.google.com/file/d/copia/view');
    await submit();
    await vi.waitFor(() => expect(api.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(true));
    const {body} = api.mock.calls.find(([, options]) => options?.method === 'POST')[1];
    expect(body.preparation_status).toBe('enviado_fisico');
    // One date serves as the document and sending date; the form no longer asks for both.
    expect(body.date).toBe('2026-10-12');
    expect(body.sent_date).toBeUndefined();
    expect(body.approval_status).toBeUndefined();
    expect(document.body.textContent).not.toContain('Aprobación');
  });

  it('pide seguimiento solo cuando el documento lo necesita y lo limpia si no', async () => {
    api.mockImplementation((path) => Promise.resolve(path.includes('next-number')
      ? { automatic: true, number: 'CARTA N° 503-2026-UNAJMA-OGC' } : { id: 'doc' }));
    await open();
    await vi.waitFor(() => expect(input('Número').value).toContain('503'));
    const hasLabel = (text) => [...document.querySelectorAll('.q-field__label, label')].some((el) => el.textContent.includes(text));
    expect(hasLabel('Fecha límite de respuesta')).toBe(false);
    const toggle = () => [...document.querySelectorAll('.q-checkbox')].find((el) => el.textContent.includes('necesita seguimiento'));
    toggle().click();
    await vi.waitFor(() => expect(hasLabel('Fecha límite de respuesta')).toBe(true));
    toggle().click();
    await vi.waitFor(() => expect(hasLabel('Fecha límite de respuesta')).toBe(false));
    await fill('Asunto del documento', 'Carta sin seguimiento');
    await choose('Destinatario', 'Rectorado');
    await submit();
    await vi.waitFor(() => expect(api.mock.calls.some(([, options]) => options?.method === 'POST')).toBe(true));
    const { body } = api.mock.calls.find(([, options]) => options?.method === 'POST')[1];
    expect(body.followup_frequency).toBeNull();
    expect(body.due_date).toBeNull();
  });
});
