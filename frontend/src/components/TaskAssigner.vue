<script setup>
  defineProps({ record: Object });
</script>
<template>
  <p class="task-assigner">
    <q-icon name="person_outline" aria-hidden="true" /><span
      >Asignada por: <b>{{ record?._labels?.created_by || 'No registrado' }}</b></span
    >
  </p>
</template>
