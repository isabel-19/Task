<script setup>
  import { ref } from 'vue';
  import { api } from '../api';
  const configuration = ref(null),
    form = ref({}),
    loading = ref(false),
    saving = ref(false),
    error = ref(''),
    saved = ref(false);
  const secretFields = ['google_client_secret', 'google_picker_api_key', 'microsoft_client_secret'];
  const providers = [
    {
      id: 'google',
      title: 'Google Drive y Docs',
      fields: [
        ['google_client_id', 'ID de cliente Google'],
        ['google_client_secret', 'Secreto de cliente Google'],
        ['google_picker_api_key', 'Clave de Google Picker'],
        ['google_project_number', 'Número del proyecto Google'],
      ],
    },
    {
      id: 'microsoft',
      title: 'Microsoft / Outlook y OneDrive',
      fields: [
        ['microsoft_client_id', 'ID de aplicación'],
        ['microsoft_client_secret', 'Secreto de cliente'],
        ['microsoft_tenant', 'Directorio Microsoft'],
      ],
    },
  ];
  function apply(result) {
    configuration.value = result;
    form.value = { ...result.fields, ...Object.fromEntries(secretFields.map((key) => [key, ''])) };
    form.value.cloud_frontend_url ||= window.location.origin;
    form.value.cloud_public_api_url ||= window.location.origin + '/api';
  }
  async function load() {
    loading.value = true;
    error.value = '';
    try {
      apply(await api('/cloud/configuration'));
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }
  const emit = defineEmits(['saved']);
  async function save() {
    saving.value = true;
    error.value = '';
    saved.value = false;
    try {
      const body = { ...form.value, revision: configuration.value.revision };
      for (const key of secretFields) if (!body[key]) delete body[key];
      apply(await api('/cloud/configuration', { method: 'POST', body }));
      saved.value = true;
      emit('saved');
    } catch (e) {
      error.value = e.message;
    } finally {
      saving.value = false;
    }
  }
</script>
<template>
  <q-expansion-item
    class="panel q-mt-lg"
    icon="settings"
    label="Habilitar conexiones para todos los usuarios"
    caption="Solo jefatura y administración · configuración única"
    @show="load"
  >
    <div class="q-pa-md">
      <p>
        Registra una aplicación de Google o Microsoft para esta oficina y completa sus datos aquí
        una sola vez. Después, cada persona con permiso para trabajar en tareas podrá conectar su
        propia cuenta y autorizar sus documentos.
      </p>
      <p>
        Estas conexiones permiten adjuntar documentos; el ingreso al sistema sigue usando la cuenta
        de usuario de la oficina.
      </p>
      <q-linear-progress
        v-if="loading"
        indeterminate
        aria-label="Cargando configuración de conexiones"
      />
      <q-banner v-if="error" class="error-banner q-mb-md" role="alert"
        >{{ error
        }}<template #action
          ><q-btn flat no-caps label="Recargar configuración" @click="load" /></template
      ></q-banner>
      <q-banner v-if="saved" class="info-note q-mb-md" role="status"
        >Configuración guardada. Los proveedores completos ya están disponibles para los usuarios
        autorizados.</q-banner
      >
      <q-form v-if="configuration && !loading" class="cloud-configuration-form" @submit="save">
        <q-banner v-if="!configuration.encryption_ready" class="error-banner q-mb-md"
          >Falta habilitar el cifrado en el servidor. Administración debe ejecutar
          scripts/setup-cloud-local.py antes de guardar.</q-banner
        >
        <div class="cloud-account-grid q-mb-lg">
          <q-input
            v-model="form.cloud_frontend_url"
            outlined
            label="Dirección de la aplicación"
            hint="Ejemplo: https://agenda.oficina.edu.pe"
            :disable="saving"
          />
          <q-input
            v-model="form.cloud_public_api_url"
            outlined
            label="Dirección pública de la API"
            hint="Ejemplo: https://agenda.oficina.edu.pe/api"
            :disable="saving"
          />
        </div>
        <div class="cloud-account-grid">
          <section v-for="provider in providers" :key="provider.id" class="cloud-account-card">
            <h2>{{ provider.title }}</h2>
            <q-badge
              :color="configuration.providers[provider.id].configured ? 'positive' : 'warning'"
              :text-color="configuration.providers[provider.id].configured ? 'white' : 'black'"
              class="q-mb-md"
              >{{
                configuration.providers[provider.id].configured
                  ? 'Habilitado para todos los usuarios autorizados'
                  : 'Configuración pendiente'
              }}</q-badge
            >
            <q-input
              v-for="[key, label] in provider.fields"
              :key="key"
              v-model="form[key]"
              outlined
              :label="label"
              :type="secretFields.includes(key) ? 'password' : 'text'"
              autocomplete="off"
              :disable="saving"
              class="q-mb-md"
              :hint="
                secretFields.includes(key)
                  ? configuration.saved_secrets[key]
                    ? 'Credencial guardada. Deja vacío para conservarla.'
                    : 'Aún no se ha guardado esta credencial.'
                  : undefined
              "
            />
            <p class="text-weight-medium">
              Dirección de retorno para registrar en
              {{ provider.id === 'google' ? 'Google' : 'Microsoft' }}:
            </p>
            <p class="cloud-callback">
              {{ form.cloud_public_api_url?.replace(/\/$/, '') }}/cloud/{{ provider.id }}/callback
            </p>
          </section>
        </div>
        <p class="info-note q-mt-lg">
          Google y Microsoft requieren que el propietario del sistema registre la aplicación y sus
          permisos. Algunos documentos institucionales requieren autorización de su organización.
          Cambiar el ID de una aplicación o el directorio Microsoft pedirá a sus usuarios volver a
          conectar; las evidencias entregadas se conservan.
        </p>
        <q-btn
          type="submit"
          unelevated
          no-caps
          color="primary"
          label="Guardar configuración general"
          :loading="saving"
          :disable="!configuration.encryption_ready"
        />
      </q-form>
    </div>
  </q-expansion-item>
</template>
<style scoped>
  .cloud-callback {
    overflow-wrap: anywhere;
  }
  .cloud-account-grid {
    align-items: start;
  }
</style>
