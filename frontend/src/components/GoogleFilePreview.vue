<script setup>
  import { computed } from 'vue';
  import EvidencePreview from './EvidencePreview.vue';
  const props = defineProps({ modelValue: Boolean, document: Object });
  const emit = defineEmits(['update:modelValue']);
  const file = computed(() =>
    props.document
      ? {
          id: props.document.id,
          name: props.document.name,
          cloud: { item_id: props.document.id },
          url: 'https://drive.google.com/file/d/' + encodeURIComponent(props.document.id) + '/view',
        }
      : null,
  );
</script>
<template>
  <EvidencePreview
    :model-value="modelValue"
    :file="file"
    @update:model-value="(value) => emit('update:modelValue', value)"
  />
</template>
