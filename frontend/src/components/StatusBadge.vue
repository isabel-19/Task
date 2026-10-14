<script setup>
  import { computed } from 'vue';
  import { human } from '../modules';
  const props = defineProps({ value: String });
  const type = computed(() =>
    [
      'cerrada',
      'validada',
      'validado',
      'cumplido',
      'conforme',
      'aprobado',
      'atendido',
      'finalizado',
    ].includes(props.value)
      ? 'success'
      : ['observado', 'observada', 'urgente', 'alta'].includes(props.value)
        ? 'danger'
        : ['en_revision', 'pendiente_validacion', 'solicitada', 'firma'].includes(props.value)
          ? 'warning'
          : ['en_progreso', 'remitido', 'derivacion', 'revision'].includes(props.value)
            ? 'info'
            : 'neutral',
  );
</script>
<template>
  <span class="status-badge" :class="type"
    ><span class="status-dot"></span>{{ human(value || 'pendiente') }}</span
  >
</template>
