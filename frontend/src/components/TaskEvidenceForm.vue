<script setup>
  import { reactive, ref, watch, nextTick, computed } from 'vue';
  import { api, session } from '../api';
  import CloudFilePicker from './CloudFilePicker.vue';
  const props = defineProps({ record: Object, uploadOptions: Object });
  const emit = defineEmits(['saved']);
  const form = reactive({ comment: '', progress: 0, url: '', access: false });
  const mode = ref('file'),
    upload = ref(null);
  const cloudFile = ref(null);
  watch(
    () => props.uploadOptions?.enabled,
    (enabled) => {
      if (enabled === false) mode.value = 'link';
    },
    { immediate: true },
  );
  const maxBytes = computed(() => props.uploadOptions?.max_bytes || 20 * 1024 * 1024);
  const extensions = computed(
    () =>
      props.uploadOptions?.extensions || [
        '.pdf',
        '.png',
        '.jpg',
        '.jpeg',
        '.webp',
        '.docx',
        '.xlsx',
        '.txt',
        '.csv',
      ],
  );
  const busy = ref(false),
    error = ref(''),
    saved = ref(false),
    evidenceForm = ref(null);
  watch(
    () => props.record.id,
    () => {
      form.comment = '';
      form.url = '';
      form.access = false;
      upload.value = null;
      cloudFile.value = null;
      form.progress =
        props.record.participants?.find((person) => person.id === session.user?.id)
          ?.reported_progress || 0;
      error.value = '';
      saved.value = false;
    },
    { immediate: true },
  );
  watch(mode, async () => {
    error.value = '';
    await nextTick();
    evidenceForm.value?.resetValidation();
  });
  const required = [(value) => Boolean(String(value || '').trim()) || 'Completa este campo.'];
  function validUrl(value) {
    try {
      const url = new URL(value);
      return (
        (url.protocol === 'https:' &&
          ['drive.google.com', 'docs.google.com'].includes(url.hostname) &&
          !url.username &&
          !url.password) ||
        'Usa un enlace HTTPS de Drive o Docs.'
      );
    } catch {
      return 'Usa un enlace HTTPS de Drive o Docs.';
    }
  }
  async function submit() {
    if (mode.value === 'link' && !form.access) {
      error.value = 'Confirma que las personas que revisan pueden abrir el enlace.';
      return;
    }
    if (mode.value === 'file' && !upload.value) {
      error.value = 'Selecciona un archivo de tu equipo.';
      return;
    }
    if (mode.value === 'cloud' && !cloudFile.value) {
      error.value = 'Elige un documento de tu cuenta vinculada.';
      return;
    }
    busy.value = true;
    error.value = '';
    saved.value = false;
    try {
      let body;
      if (mode.value === 'file') {
        body = new FormData();
        body.append('revision', props.record.revision);
        body.append('progress', form.progress);
        body.append('comment', form.comment.trim());
        body.append('file', upload.value);
      } else if (mode.value === 'cloud') {
        body = {
          revision: props.record.revision,
          progress: Number(form.progress),
          comment: form.comment.trim(),
          provider: cloudFile.value.provider,
          item_id: cloudFile.value.id,
        };
      } else {
        body = {
          revision: props.record.revision,
          progress: Number(form.progress),
          comment: form.comment.trim(),
          evidence: { url: form.url.trim(), access_confirmed: true },
        };
      }
      const result = await api(
        '/tasks/' +
          props.record.id +
          (mode.value === 'file'
            ? '/advance-file'
            : mode.value === 'cloud'
              ? '/advance-cloud'
              : '/advance'),
        {
          method: 'POST',
          body,
        },
      );
      form.comment = '';
      form.url = '';
      form.access = false;
      upload.value = null;
      cloudFile.value = null;
      saved.value = true;
      emit('saved', result);
      window.dispatchEvent(new Event('ogc:task-review-changed'));
      await nextTick();
      evidenceForm.value?.resetValidation();
    } catch (e) {
      error.value = e.message;
    } finally {
      busy.value = false;
    }
  }
</script>
<template>
  <section class="my-task-evidence q-mt-lg">
    <h3>Añadir mi evidencia</h3>
    <p class="info-note">
      Describe brevemente tu entrega y adjunta un archivo del equipo, un documento de tu cuenta
      vinculada o un enlace. Al enviarla quedará pendiente de revisión por jefatura; su respuesta
      aparecerá en «Evidencias».
    </p>
    <q-form ref="evidenceForm" class="q-gutter-y-md" @submit="submit">
      <q-btn-toggle
        v-model="mode"
        class="evidence-source-toggle"
        no-caps
        unelevated
        toggle-color="primary"
        :disable="busy"
        :options="[
          {
            label: 'Archivo de mi equipo',
            value: 'file',
            icon: 'upload_file',
            disable: uploadOptions?.enabled === false,
          },
          { label: 'Enlace Drive/Docs', value: 'link', icon: 'link' },
          {
            label: 'Google / Microsoft',
            value: 'cloud',
            icon: 'cloud',
            disable: uploadOptions?.enabled === false,
          },
        ]"
        aria-label="Tipo de evidencia"
      />
      <q-input
        v-model="form.comment"
        outlined
        autogrow
        type="textarea"
        label="Descripción de mi entrega *"
        maxlength="5000"
        :rules="required"
        :disable="busy"
      />
      <q-input
        v-model="form.progress"
        outlined
        type="number"
        min="0"
        max="100"
        label="Mi avance (%) *"
        :rules="[
          (value) =>
            (String(value).trim() !== '' &&
              Number.isInteger(Number(value)) &&
              Number(value) >= 0 &&
              Number(value) <= 100) ||
            'Indica un porcentaje entre 0 y 100.',
        ]"
        :disable="busy"
      />
      <q-file
        v-if="mode === 'file'"
        v-model="upload"
        outlined
        clearable
        use-chips
        label="Seleccionar archivo de mi equipo *"
        :accept="extensions.join(',')"
        :max-file-size="maxBytes"
        :disable="busy"
        :rules="[(value) => Boolean(value) || 'Selecciona un archivo.']"
        @rejected="error = `El archivo no se admite o supera ${maxBytes / 1024 / 1024} MB.`"
      >
        <template #prepend><q-icon name="upload_file" /></template>
      </q-file>
      <p v-if="mode === 'file'" class="evidence-upload-help">
        {{ extensions.join(', ').replaceAll('.', '').toUpperCase() }} · Máximo
        {{ maxBytes / 1024 / 1024 }} MB. Después de enviarlo podrás previsualizarlo y descargarlo
        desde Evidencias.
      </p>
      <CloudFilePicker v-if="mode === 'cloud'" v-model="cloudFile" :disabled="busy" />
      <q-input
        v-if="mode === 'link'"
        v-model="form.url"
        outlined
        label="Enlace de mi evidencia (Drive o Docs) *"
        :rules="[...required, validUrl]"
        :disable="busy"
      />
      <q-checkbox
        v-if="mode === 'link'"
        v-model="form.access"
        label="Las personas que revisan pueden abrir este enlace"
        :disable="busy"
      />
      <div>
        <q-btn
          type="submit"
          color="primary"
          unelevated
          no-caps
          icon="attach_file"
          label="Enviar evidencia a revisión"
          :loading="busy"
        />
      </div>
    </q-form>
    <q-banner v-if="saved" class="q-mt-md bg-blue-1" role="status"
      >Tu evidencia se guardó. Está pendiente de revisión y jefatura recibirá un aviso en la
      campana.</q-banner
    >
    <q-banner v-if="error" class="error-banner q-mt-md" role="alert">{{ error }}</q-banner>
  </section>
</template>
