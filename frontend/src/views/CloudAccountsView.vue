<script setup>
  import { ref, onMounted, onUnmounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { api, can } from '../api';
  import CloudConfigurationPanel from '../components/CloudConfigurationPanel.vue';
  import GoogleFilePreview from '../components/GoogleFilePreview.vue';
  import { selectGoogleFile } from '../googlePicker';
  const route = useRoute();
  const accounts = ref([]),
    loading = ref(true),
    busy = ref(''),
    error = ref(''),
    removing = ref(null);
  const previewDocument = ref(null),
    previewOpen = ref(false);
  const names = {
    google: 'Google Drive y Google Docs',
    microsoft: 'Microsoft / Outlook y OneDrive',
  };
  let active = true;
  async function load() {
    loading.value = true;
    error.value = '';
    try {
      const result = await api('/cloud/accounts');
      if (active) accounts.value = result.items;
    } catch (e) {
      if (active) error.value = e.message;
    } finally {
      if (active) loading.value = false;
    }
  }
  async function connect(provider) {
    busy.value = provider;
    error.value = '';
    try {
      const result = await api('/cloud/' + provider + '/connect', { method: 'POST' });
      window.location.assign(result.authorization_url);
    } catch (e) {
      error.value = e.message;
      busy.value = '';
    }
  }
  async function unlink() {
    busy.value = removing.value.provider;
    error.value = '';
    try {
      await api('/cloud/' + removing.value.provider + '/disconnect', { method: 'POST' });
      removing.value = null;
      await load();
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = '';
    }
  }
  async function exploreGoogle() {
    busy.value = 'google';
    error.value = '';
    try {
      const credentials = await api('/cloud/google/picker', { method: 'POST' });
      const item = await selectGoogleFile(credentials);
      if (active && item) {
        previewDocument.value = item;
        previewOpen.value = true;
      }
    } catch (e) {
      if (active) error.value = e.message;
    } finally {
      if (active) busy.value = '';
    }
  }
  onMounted(load);
  onUnmounted(() => {
    active = false;
  });
</script>
<template>
  <q-page class="content-page cloud-accounts-page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">TUS DOCUMENTOS</span>
        <h1>Cuentas vinculadas<span class="title-dot">.</span></h1>
        <p>
          Conecta tu propia cuenta para consultar archivos tuyos o compartidos contigo y usarlos
          como evidencia.
        </p>
      </div>
      <q-btn outline no-caps color="primary" to="/tareas" label="Ir a mis tareas" icon="task_alt" />
    </div>
    <q-banner v-if="route.query.status === 'connected'" class="info-note q-mb-lg" role="status"
      >Cuenta vinculada. Ya puedes elegir sus documentos desde Añadir evidencia.</q-banner
    >
    <q-banner v-else-if="route.query.status === 'cancelled'" class="info-note q-mb-lg" role="status"
      >Se canceló la autorización. Puedes volver a conectar cuando quieras.</q-banner
    >
    <q-banner v-if="route.query.status === 'failed'" class="error-banner q-mb-lg" role="alert"
      >No se pudo completar la conexión con el proveedor. Vuelve a conectar tu cuenta; si el
      problema continúa, comunícalo a administración.</q-banner
    >
    <q-linear-progress v-if="loading" indeterminate aria-label="Cargando cuentas vinculadas" />
    <q-banner v-if="error" class="error-banner q-mb-lg" role="alert"
      >{{ error
      }}<template #action><q-btn flat no-caps label="Actualizar" @click="load" /></template
    ></q-banner>
    <div class="cloud-account-grid">
      <article v-for="account in accounts" :key="account.provider" class="panel cloud-account-card">
        <q-icon
          :name="account.provider === 'google' ? 'add_to_drive' : 'cloud'"
          size="36px"
          color="primary"
        />
        <h2>{{ names[account.provider] }}</h2>
        <p v-if="account.connected"><b>Conectada:</b> {{ account.account_label }}</p>
        <p v-else>Cuenta sin vincular</p>
        <p>
          {{
            account.provider === 'google'
              ? 'Explora tus archivos, Compartidos conmigo y unidades compartidas, según los permisos de tu cuenta de Google.'
              : 'Elige archivos de OneDrive. Los adjuntos recibidos por Outlook deben guardarse primero en OneDrive.'
          }}
        </p>
        <p v-if="!account.configured" class="info-note">
          La conexión está pendiente de habilitación por administración.
        </p>
        <div class="row q-gutter-sm">
          <q-btn
            v-if="account.configured && can('tasks.write')"
            color="primary"
            unelevated
            no-caps
            :label="account.connected ? 'Volver a autorizar' : 'Conectar cuenta'"
            :loading="busy === account.provider"
            :disable="Boolean(busy)"
            @click="connect(account.provider)"
          /><q-btn
            v-if="
              account.provider === 'google' &&
              account.connected &&
              account.configured &&
              can('tasks.write')
            "
            outline
            no-caps
            color="primary"
            icon="visibility"
            label="Explorar y previsualizar"
            :disable="Boolean(busy)"
            @click="exploreGoogle"
          /><q-btn
            v-if="account.connected"
            outline
            color="primary"
            no-caps
            label="Desvincular"
            :disable="Boolean(busy)"
            @click="removing = account"
          />
        </div>
      </article>
    </div>
    <p class="info-note q-mt-lg">
      Cada persona conecta sus propias cuentas. Al presentar una evidencia se conserva una copia del
      archivo para su revisión. Desvincular una cuenta no elimina las evidencias ya entregadas.
    </p>
    <p v-if="!can('tasks.write')" class="info-note">
      Tu permiso actual permite consultar tareas. Para adjuntar documentos necesitas permiso para
      trabajar en tareas.
    </p>
    <CloudConfigurationPanel v-if="can('admin.write')" @saved="load" />
    <GoogleFilePreview v-model="previewOpen" :document="previewDocument" />
    <q-dialog
      :model-value="Boolean(removing)"
      :persistent="Boolean(busy)"
      @update:model-value="
        (value) => {
          if (!value) removing = null;
        }
      "
      ><q-card class="action-form"
        ><q-card-section
          ><h2>Desvincular cuenta</h2>
          <p>
            Dejarás de seleccionar nuevos documentos de {{ removing?.account_label }}. Las
            evidencias ya entregadas se conservan.
          </p></q-card-section
        ><q-card-actions align="right"
          ><q-btn
            flat
            no-caps
            label="Cancelar"
            :disable="Boolean(busy)"
            @click="removing = null" /><q-btn
            color="primary"
            no-caps
            label="Desvincular cuenta"
            :loading="Boolean(busy)"
            @click="unlink" /></q-card-actions></q-card
    ></q-dialog>
  </q-page>
</template>
