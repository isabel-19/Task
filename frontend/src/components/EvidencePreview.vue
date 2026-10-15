<script setup>
  import { ref, watch, onUnmounted } from 'vue';
  import { api, fileUrl } from '../api';
  const props = defineProps({ modelValue: Boolean, file: Object });
  const emit = defineEmits(['update:modelValue']);
  const loading = ref(false),
    error = ref(''),
    source = ref(''),
    contentType = ref(''),
    preview = ref(null);
  let sequence = 0,
    controller;
  function release() {
    controller?.abort();
    if (source.value) URL.revokeObjectURL(source.value);
    source.value = '';
    preview.value = null;
    contentType.value = '';
  }
  async function load() {
    const turn = ++sequence;
    release();
    if (!props.modelValue || !props.file) return;
    controller = new AbortController();
    loading.value = true;
    error.value = '';
    try {
      if (props.file.cloud) {
        const blob = await api('/cloud/google/preview', {
          method: 'POST',
          body: { item_id: props.file.cloud.item_id },
          responseType: 'blob',
          signal: controller.signal,
        });
        if (turn !== sequence) return;
        contentType.value = blob.type;
        if (blob.type.startsWith('application/json')) {
          const data = JSON.parse(await blob.text());
          if (turn === sequence) preview.value = data;
        } else {
          source.value = URL.createObjectURL(blob);
        }
        return;
      }
      contentType.value = props.file.content_type;
      const path = '/evidence-files/' + props.file.id;
      if (
        props.file.content_type === 'application/pdf' ||
        props.file.content_type.startsWith('image/')
      ) {
        const blob = await api(path, { responseType: 'blob', signal: controller.signal });
        if (turn === sequence) source.value = URL.createObjectURL(blob);
      } else {
        const data = await api(path + '/preview', { signal: controller.signal });
        if (turn === sequence) preview.value = data;
      }
    } catch (e) {
      if (turn === sequence && e.name !== 'AbortError') error.value = e.message;
    } finally {
      if (turn === sequence) loading.value = false;
    }
  }
  watch([() => props.modelValue, () => props.file?.id], load, { immediate: true });
  onUnmounted(() => {
    sequence++;
    release();
  });
</script>
<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <q-card class="evidence-preview-dialog">
      <q-card-section class="row items-center no-wrap q-gutter-md">
        <div class="evidence-preview-heading">
          <span class="eyebrow">{{
            file?.cloud ? 'VISTA PREVIA DE GOOGLE DRIVE' : 'VISTA PREVIA DE EVIDENCIA'
          }}</span>
          <h2>{{ file?.name }}</h2>
        </div>
        <q-space /><q-btn flat round icon="close" aria-label="Cerrar vista previa" v-close-popup />
      </q-card-section>
      <q-separator />
      <q-card-section class="evidence-preview-content" :aria-busy="loading">
        <q-linear-progress v-if="loading" indeterminate aria-label="Cargando vista previa" />
        <q-banner v-else-if="error" class="error-banner" role="alert"
          >{{ error
          }}<template #action><q-btn flat no-caps label="Reintentar" @click="load" /></template
        ></q-banner>
        <img
          v-else-if="source && contentType.startsWith('image/')"
          :src="source"
          :alt="`Evidencia: ${file.name}`"
          class="evidence-preview-image"
          @error="error = 'No se pudo mostrar la imagen. Puedes descargar el archivo original.'"
        />
        <div v-else-if="source" class="evidence-pdf-preview">
          <p>
            {{
              file?.cloud
                ? 'Esta vista no envía ni guarda una evidencia. Si no se muestra el PDF, usa «Abrir en Google».'
                : 'Si tu navegador no muestra el PDF, usa «Abrir original» o «Descargar».'
            }}
          </p>
          <iframe :src="source" :title="`Vista previa de ${file.name}`" />
        </div>
        <template v-else-if="preview">
          <p class="info-note">
            {{
              file?.cloud
                ? 'Vista privada del contenido. Todavía no se ha presentado como evidencia.'
                : 'Vista del contenido. Para consultar el formato completo, descarga el original.'
            }}
            {{
              preview.truncated
                ? 'La vista está limitada; el archivo original se conserva completo.'
                : ''
            }}
          </p>
          <pre v-if="preview.kind === 'text'" class="evidence-text-preview">{{
            preview.text || 'El documento no contiene texto visible.'
          }}</pre>
          <section
            v-for="(sheet, index) in preview.sheets || []"
            :key="index"
            class="evidence-sheet-preview"
          >
            <h3>{{ sheet.name }}</h3>
            <div class="evidence-table-scroll">
              <table>
                <tbody>
                  <tr v-for="(row, rowIndex) in sheet.rows" :key="rowIndex">
                    <td v-for="(cell, colIndex) in row" :key="colIndex">{{ cell }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>
      </q-card-section>
      <q-separator />
      <q-card-actions align="right" class="q-pa-md evidence-preview-actions">
        <q-btn
          v-if="file?.url"
          :href="fileUrl(file.url)"
          target="_blank"
          rel="noopener noreferrer"
          outline
          no-caps
          color="primary"
          icon="open_in_new"
          :label="file?.cloud ? 'Abrir en Google' : 'Abrir original'"
        />
        <q-btn
          v-if="file && !file.cloud"
          :href="fileUrl(file.url + '?download=true')"
          color="primary"
          unelevated
          no-caps
          icon="download"
          label="Descargar"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>
