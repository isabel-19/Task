<script setup>
  import { computed } from 'vue';
  import { dayKey, weekDays } from '../taskAgenda';
  import StatusBadge from './StatusBadge.vue';
  import TaskEvidenceActions from './TaskEvidenceActions.vue';
  import TaskAssigner from './TaskAssigner.vue';
  const props = defineProps({ rows: Array, start: Date, loading: Boolean, pagination: Object });
  const emit = defineEmits(['open', 'submit', 'evidence', 'page']);
  const today = computed(() => dayKey(new Date()));
  const days = computed(() =>
    weekDays(props.start).map((day) => ({
      ...day,
      rows: (props.rows || [])
        .filter((row) => row.due_date === day.key)
        .sort((a, b) => a.title.localeCompare(b.title, 'es')),
    })),
  );
</script>
<template>
  <section class="task-agenda" aria-label="Agenda semanal de tareas" :aria-busy="loading">
    <q-linear-progress v-if="loading" indeterminate aria-label="Cargando agenda" />
    <p class="agenda-caption">
      Tareas por fecha límite · {{ pagination.rowsNumber }} en esta semana
    </p>
    <section
      v-for="day in days"
      :key="day.key"
      class="agenda-day"
      :class="{ 'agenda-today': day.key === today }"
    >
      <h3>{{ day.label }} <span v-if="day.key === today">Hoy</span></h3>
      <div class="agenda-day-tasks">
        <p v-if="!day.rows.length" class="agenda-empty">
          {{ loading ? 'Cargando…' : 'Sin tareas para este día' }}
        </p>
        <article v-for="row in day.rows" :key="row.id" class="agenda-task">
          <button class="agenda-task-title" @click="emit('open', row)">{{ row.title }}</button>
          <p>{{ row.participants?.map((person) => person.name).join(', ') }}</p>
          <TaskAssigner :record="row" />
          <div class="row items-center q-gutter-sm">
            <StatusBadge :value="row.status" /><StatusBadge
              v-if="day.key < today && row.status !== 'cerrada'"
              value="vencida"
            />
          </div>
          <TaskEvidenceActions :record="row" @open="emit('evidence', row)" />
          <q-btn
            v-if="row.can_advance"
            outline
            color="primary"
            no-caps
            size="sm"
            icon="attach_file"
            label="Añadir evidencia"
            @click="emit('submit', row)"
          />
        </article>
      </div>
    </section>
    <div v-if="pagination.rowsNumber > pagination.rowsPerPage" class="q-pa-md">
      <p>Esta semana tiene más tareas. Consulta las siguientes páginas.</p>
      <q-pagination
        :model-value="pagination.page"
        :max="Math.ceil(pagination.rowsNumber / pagination.rowsPerPage)"
        :max-pages="5"
        @update:model-value="emit('page', $event)"
      />
    </div>
  </section>
</template>
