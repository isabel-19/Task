import { afterEach, expect, it, vi } from 'vitest';
let callbacks, picker;
function googleSdk() {
  callbacks = { views: [] };
  picker = { setVisible: vi.fn(), dispose: vi.fn() };
  class DocsView {
    setIncludeFolders() {
      return this;
    }
    setSelectFolderEnabled() {
      return this;
    }
    setLabel(value) {
      this.label = value;
      return this;
    }
    setOwnedByMe(value) {
      this.ownedByMe = value;
      return this;
    }
    setEnableDrives(value) {
      this.sharedDrives = value;
      return this;
    }
  }
  class PickerBuilder {
    addView(view) {
      callbacks.views.push(view);
      return this;
    }
    setOAuthToken(value) {
      callbacks.token = value;
      return this;
    }
    setDeveloperKey(value) {
      callbacks.key = value;
      return this;
    }
    setAppId(value) {
      callbacks.app = value;
      return this;
    }
    setOrigin(value) {
      callbacks.origin = value;
      return this;
    }
    setLocale(value) {
      callbacks.locale = value;
      return this;
    }
    setCallback(value) {
      callbacks.respond = value;
      return this;
    }
    build() {
      return picker;
    }
  }
  return {
    picker: {
      DocsView,
      PickerBuilder,
      ViewId: { DOCS: 'docs' },
      Action: { PICKED: 'picked', CANCEL: 'cancel' },
    },
  };
}
afterEach(() => {
  delete window.google;
  delete window.gapi;
  document
    .querySelectorAll('script[src="https://apis.google.com/js/api.js"]')
    .forEach((node) => node.remove());
  vi.useRealTimers();
  vi.resetModules();
});
const credentials = {
  access_token: 'ephemeral-fixture',
  api_key: 'public-picker-key',
  app_id: '123',
};
it('usa el SDK oficial y devuelve el documento seleccionado sin poner tokens en el DOM', async () => {
  window.google = googleSdk();
  const { selectGoogleFile } = await import('../googlePicker');
  const result = selectGoogleFile(credentials);
  await vi.waitFor(() => expect(picker.setVisible).toHaveBeenCalledWith(true));
  expect(callbacks.token).toBe(credentials.access_token);
  expect(callbacks.origin).toBe(window.location.origin);
  expect(callbacks.locale).toBe('es');
  expect(callbacks.views.map((view) => view.label)).toEqual([
    'Todos los archivos',
    'Compartidos conmigo',
    'Unidades compartidas',
  ]);
  expect(callbacks.views[0].ownedByMe).toBeUndefined();
  expect(callbacks.views[1].ownedByMe).toBe(false);
  expect(callbacks.views[2].sharedDrives).toBe(true);
  expect(callbacks.views[2].ownedByMe).toBeUndefined();
  callbacks.respond({ action: 'picked', docs: [{ id: 'doc-1', name: 'Informe' }] });
  expect(await result).toEqual({ provider: 'google', id: 'doc-1', name: 'Informe' });
  expect(picker.dispose).toHaveBeenCalledOnce();
  expect(document.documentElement.outerHTML).not.toContain(credentials.access_token);
});
it('cerrar el selector cancela la selección y libera el visor del proveedor', async () => {
  window.google = googleSdk();
  const { selectGoogleFile } = await import('../googlePicker');
  const result = selectGoogleFile(credentials);
  await vi.waitFor(() => expect(callbacks.respond).toBeDefined());
  callbacks.respond({ action: 'cancel' });
  expect(await result).toBeNull();
  expect(picker.dispose).toHaveBeenCalledOnce();
});
it('carga Picker solo cuando hace falta y espera a que el SDK termine de inicializarse', async () => {
  window.gapi = {
    load: vi.fn((name, options) => {
      expect(name).toBe('picker');
      window.google = googleSdk();
      options.callback();
    }),
  };
  const { selectGoogleFile } = await import('../googlePicker');
  const result = selectGoogleFile(credentials);
  document
    .querySelector('script[src="https://apis.google.com/js/api.js"]')
    .dispatchEvent(new Event('load'));
  await vi.waitFor(() => expect(callbacks.respond).toBeDefined());
  callbacks.respond({ action: 'cancel' });
  expect(await result).toBeNull();
});
it('un bloqueo de red muestra error y permite reintentar en vez de esperar indefinidamente', async () => {
  vi.useFakeTimers();
  const { selectGoogleFile } = await import('../googlePicker');
  const result = selectGoogleFile(credentials);
  const assertion = expect(result).rejects.toThrow('No se pudo cargar el selector de Google');
  await vi.advanceTimersByTimeAsync(15000);
  await assertion;
  expect(document.querySelector('script[src="https://apis.google.com/js/api.js"]')).toBeNull();
  window.google = googleSdk();
  const retry = selectGoogleFile(credentials);
  await Promise.resolve();
  callbacks.respond({ action: 'cancel' });
  expect(await retry).toBeNull();
});
