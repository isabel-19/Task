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
      'enviado_digital',
      'enviado_fisico',
      'enviado_fisico_y_digital',
      'compartido',
      'enviado',
    ].includes(props.value)
      ? 'success'
      : ['pendiente', 'vencida', 'vencido', 'observado', 'observada', 'urgente', 'alta'].includes(
            props.value,
          )
        ? 'danger'
        : [
              'en_progreso',
              'pendiente_revision',
              'pendiente_validacion',
              'solicitada',
              'firma',
              'listo_para_envio',
              'para_revision',
            ].includes(props.value)
          ? 'warning'
          : [
                'en_revision',
                'remitido',
                'derivacion',
                'revision',
                'en_redaccion',
                'en_reunion',
              ].includes(props.value)
            ? 'info'
            : 'neutral',
  );
</script>
<template>
  <span class="status-badge" :class="type"
    ><span class="status-dot"></span>{{ human(value || 'pendiente') }}</span
  >
</template>
