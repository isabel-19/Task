<script setup>
  import { ref } from 'vue';
  import { fileUrl } from '../api';
  import EvidencePreview from './EvidencePreview.vue';
  defineProps({
    file: Object,
    url: String,
    label: { type: String, default: 'Abrir evidencia' },
    compact: Boolean,
  });
  const previewOpen = ref(false);
  const sizeLabel = (value) =>
    value >= 1024 * 1024
      ? `${(value / 1024 / 1024).toFixed(1)} MB`
      : `${Math.max(1, Math.round(value / 1024))} KB`;
</script>
<template>
  <div class="evidence-attachment" @click.stop>
    <template v-if="file">
      <span class="evidence-file-name"
        >{{ file.name }} <small>· {{ sizeLabel(file.size) }}</small></span
      >
      <div class="row items-center q-gutter-sm">
        <q-btn
          color="primary"
          unelevated
          no-caps
          icon="visibility"
          label="Previsualizar"
          :size="compact ? 'sm' : undefined"
          @click="previewOpen = true"
        />
        <q-btn
          :href="fileUrl(file.url + '?download=true')"
          outline
          color="primary"
          no-caps
          icon="download"
          :label="compact ? undefined : 'Descargar'"
          aria-label="Descargar archivo"
          :size="compact ? 'sm' : undefined"
        />
      </div>
      <a
        v-if="file.source?.url"
        class="cloud-source-link"
        :href="file.source.url"
        target="_blank"
        rel="noopener noreferrer"
        >{{ file.source.provider === 'google' ? 'Origen: Google Drive' : 'Origen: OneDrive' }}
        <q-icon name="open_in_new"
      /></a>
      <EvidencePreview v-if="previewOpen" v-model="previewOpen" :file="file" />
    </template>
    <q-btn
      v-else-if="url"
      :href="fileUrl(url)"
      target="_blank"
      rel="noopener noreferrer"
      color="primary"
      unelevated
      no-caps
      icon="description"
      icon-right="open_in_new"
      :label="label"
      :size="compact ? 'sm' : undefined"
      :class="{ 'evidence-open-button': !compact }"
    />
  </div>
</template>
