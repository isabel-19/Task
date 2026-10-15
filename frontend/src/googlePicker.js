let loading;
function loadPicker() {
  if (window.google?.picker) return Promise.resolve();
  if (loading) return loading;
  loading = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://apis.google.com/js/api.js';
    script.async = true;
    const fail = () => {
      clearTimeout(timer);
      script.remove();
      loading = null;
      reject(new Error('No se pudo cargar el selector de Google. Intenta nuevamente.'));
    };
    const timer = setTimeout(fail, 15000);
    script.onerror = fail;
    script.onload = () => {
      clearTimeout(timer);
      if (!window.gapi?.load) return fail();
      window.gapi.load('picker', {
        callback: resolve,
        onerror: fail,
        timeout: 15000,
        ontimeout: fail,
      });
    };
    document.head.append(script);
  });
  return loading;
}
export async function selectGoogleFile(credentials) {
  await loadPicker();
  return new Promise((resolve) => {
    let picker;
    picker = new window.google.picker.PickerBuilder()
      .addView(
        new window.google.picker.DocsView(window.google.picker.ViewId.DOCS)
          .setIncludeFolders(true)
          .setSelectFolderEnabled(false)
          .setLabel('Todos los archivos'),
      )
      .addView(
        new window.google.picker.DocsView(window.google.picker.ViewId.DOCS)
          .setIncludeFolders(true)
          .setSelectFolderEnabled(false)
          .setOwnedByMe(false)
          .setLabel('Compartidos conmigo'),
      )
      .addView(
        new window.google.picker.DocsView(window.google.picker.ViewId.DOCS)
          .setIncludeFolders(true)
          .setSelectFolderEnabled(false)
          .setEnableDrives(true)
          .setLabel('Unidades compartidas'),
      )
      .setOAuthToken(credentials.access_token)
      .setDeveloperKey(credentials.api_key)
      .setAppId(credentials.app_id)
      .setOrigin(window.location.origin)
      .setLocale('es')
      .setCallback((data) => {
        if (data.action === window.google.picker.Action.PICKED) {
          const item = data.docs?.[0];
          picker.dispose();
          resolve(item ? { provider: 'google', id: item.id, name: item.name } : null);
        } else if (data.action === window.google.picker.Action.CANCEL) {
          picker.dispose();
          resolve(null);
        }
      })
      .build();
    picker.setVisible(true);
  });
}
