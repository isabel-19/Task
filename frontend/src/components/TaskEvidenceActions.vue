<script setup>
  import EvidenceAttachment from './EvidenceAttachment.vue';
  defineProps({ record: Object });
  const emit = defineEmits(['open']);
</script>
<template>
  <div class="task-evidence-actions">
    <EvidenceAttachment
      v-if="record.latest_evidence_url"
      :url="record.latest_evidence_url"
      :file="record.latest_evidence_file"
      compact
      label="Abrir documento"
      @click.stop
    />
    <q-btn
      v-if="record.evidence_count || record.document_count"
      flat
      color="primary"
      no-caps
      size="sm"
      :label="
        record.document_count
          ? `Ver archivos (${(record.evidence_count || 0) + record.document_count})`
          : `Ver evidencias (${record.evidence_count})`
      "
      @click.stop="emit('open', record)"
    />
    <span v-else class="muted">Sin evidencias</span>
  </div>
</template>
