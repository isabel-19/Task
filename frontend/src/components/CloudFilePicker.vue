<script setup>
  import { ref, onMounted, onUnmounted } from 'vue';
  import { api, query } from '../api';
  import { selectGoogleFile } from '../googlePicker';
  import GoogleFilePreview from './GoogleFilePreview.vue';
  defineProps({ modelValue: Object, disabled: Boolean });
  const emit = defineEmits(['update:modelValue']);
  const accounts = ref([]),
    error = ref(''),
    loading = ref(false),
    browsing = ref(false);
  const previewOpen = ref(false);
  const files = ref([]),
    trail = ref([]),
    next = ref(null);
  let active = true,
    sequence = 0;
  const names = { google: 'Google Drive', microsoft: 'Microsoft / Outlook' };
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
  async function google() {
    loading.value = true;
    error.value = '';
    try {
      const credentials = await api('/cloud/google/picker', { method: 'POST' });
      const item = await selectGoogleFile(credentials);
      if (active && item) emit('update:modelValue', item);
    } catch (e) {
      if (active) error.value = e.message;
    } finally {
      if (active) loading.value = false;
    }
  }
  async function list(folder, cursor = null, append = false) {
    const turn = ++sequence;
    loading.value = true;
    error.value = '';
    try {
      const result = await api('/cloud/microsoft/files?' + query({ folder, cursor }));
      if (!active || turn !== sequence) return;
      files.value = append ? [...files.value, ...result.items] : result.items;
      next.value = result.next_cursor;
    } catch (e) {
      if (active && turn === sequence) error.value = e.message;
    } finally {
      if (active && turn === sequence) loading.value = false;
    }
  }
  async function microsoft() {
    trail.value = [];
    files.value = [];
    browsing.value = true;
    await list();
  }
  function folder(item) {
    trail.value.push({ id: item.id, name: item.name });
    list(item.id);
  }
  function back() {
    trail.value.pop();
    list(trail.value.at(-1)?.id);
  }
  function choose(item) {
    emit('update:modelValue', { provider: 'microsoft', id: item.id, name: item.name });
    browsing.value = false;
  }
  onMounted(load);
  onUnmounted(() => {
    active = false;
    sequence++;
  });
</script>
<template>
  <section class="cloud-file-picker">
    <p class="info-note">
      Elige un archivo propio o compartido contigo desde tu cuenta vinculada. Puedes previsualizarlo
      antes de enviar; al presentar la evidencia se adjunta una copia para revisión de jefatura.
    </p>
    <div class="cloud-provider-options">
      <article v-for="account in accounts" :key="account.provider" class="cloud-provider-option">
        <b>{{ names[account.provider] }}</b>
        <p>
          {{
            account.connected
              ? account.account_label
              : account.configured
                ? 'Cuenta sin vincular'
                : 'Pendiente de habilitación por administración'
          }}
        </p>
        <q-btn
          v-if="account.connected && account.configured"
          outline
          color="primary"
          no-caps
          :label="account.provider === 'google' ? 'Elegir en Google Drive' : 'Elegir en OneDrive'"
          :disable="disabled || loading"
          @click="account.provider === 'google' ? google() : microsoft()"
        />
        <q-btn
          v-else
          href="/cuentas"
          target="_blank"
          rel="noopener noreferrer"
          flat
          color="primary"
          no-caps
          :label="account.configured ? 'Vincular cuenta' : 'Ver cuentas vinculadas'"
        />
      </article>
    </div>
    <q-btn
      flat
      no-caps
      color="primary"
      icon="refresh"
      label="Actualizar conexiones"
      :loading="loading"
      :disable="disabled"
      @click="load"
    />
    <div v-if="modelValue" class="cloud-selected-file" role="status">
      <q-icon name="description" />
      <div>
        <b>{{ modelValue.name }}</b
        ><small>{{ names[modelValue.provider] }}</small>
      </div>
      <q-space /><q-btn
        v-if="modelValue.provider === 'google'"
        outline
        no-caps
        color="primary"
        icon="visibility"
        label="Previsualizar"
        :disable="disabled || loading"
        @click="previewOpen = true"
      /><q-btn
        flat
        round
        icon="close"
        aria-label="Quitar archivo seleccionado"
        :disable="disabled"
        @click="emit('update:modelValue', null)"
      />
    </div>
    <GoogleFilePreview
      v-model="previewOpen"
      :document="modelValue?.provider === 'google' ? modelValue : null"
    />
    <q-banner v-if="error" class="error-banner" role="alert">{{ error }}</q-banner>
    <q-dialog v-model="browsing"
      ><q-card class="cloud-browser-dialog">
        <q-card-section class="row items-center"
          ><div>
            <span class="eyebrow">ARCHIVOS DE TU CUENTA</span>
            <h2>OneDrive</h2>
          </div>
          <q-space /><q-btn
            flat
            round
            icon="close"
            aria-label="Cerrar selector de OneDrive"
            v-close-popup
        /></q-card-section>
        <q-card-section>
          <div class="row items-center q-gutter-sm">
            <q-btn
              v-if="trail.length"
              flat
              round
              icon="arrow_back"
              aria-label="Carpeta anterior"
              :disable="loading"
              @click="back"
            /><b>{{ trail.at(-1)?.name || 'Mis archivos' }}</b>
          </div>
          <q-linear-progress
            v-if="loading"
            indeterminate
            class="q-my-md"
            aria-label="Cargando archivos de OneDrive"
          />
          <q-banner v-if="error" class="error-banner" role="alert"
            >{{ error
            }}<template #action
              ><q-btn flat label="Reintentar" no-caps @click="list(trail.at(-1)?.id)" /></template
          ></q-banner>
          <q-list separator
            ><q-item
              v-for="item in files"
              :key="item.id"
              clickable
              :disable="loading || !item.supported"
              @click="item.folder ? folder(item) : choose(item)"
              ><q-item-section avatar
                ><q-icon :name="item.folder ? 'folder' : 'description'" /></q-item-section
              ><q-item-section
                ><q-item-label>{{ item.name }}</q-item-label
                ><q-item-label caption>{{
                  item.folder
                    ? 'Abrir carpeta'
                    : item.supported
                      ? 'Seleccionar como evidencia'
                      : 'Formato no admitido'
                }}</q-item-label></q-item-section
              ><q-item-section side
                ><q-icon
                  :name="
                    item.folder ? 'chevron_right' : 'add_circle_outline'
                  " /></q-item-section></q-item
          ></q-list>
          <p v-if="!loading && !files.length && !error" class="muted">
            Esta carpeta no contiene archivos.
          </p>
          <q-btn
            v-if="next"
            flat
            no-caps
            color="primary"
            label="Cargar más archivos"
            :loading="loading"
            @click="list(trail.at(-1)?.id, next, true)"
          />
        </q-card-section> </q-card
    ></q-dialog>
  </section>
</template>
<style scoped>
  .cloud-selected-file {
    flex-wrap: wrap;
  }
</style>
