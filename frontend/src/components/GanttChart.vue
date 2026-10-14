<script setup>
  import { computed } from 'vue';
  import { dateLabel } from '../modules';
  const props = defineProps({ tasks: Array });
  defineEmits(['open']);
  const day = 86400000;
  const range = computed(() => {
    const starts = props.tasks.map((t) => Date.parse(t.start_date)),
      ends = props.tasks.map((t) => Date.parse(t.due_date));
    const start = starts.length ? Math.min(...starts) : Date.now();
    const end = ends.length ? Math.max(...ends) : start + 30 * day;
    return { start, end, span: Math.max(day, end - start + day) };
  });
  const ticks = computed(() =>
    Array.from({ length: 7 }, (_, i) => new Date(range.value.start + (range.value.span * i) / 6)),
  );
  function style(t) {
    return {
      left: ((Date.parse(t.start_date) - range.value.start) / range.value.span) * 100 + '%',
      width:
        (Math.max(day, Date.parse(t.due_date) - Date.parse(t.start_date) + day) /
          range.value.span) *
          100 +
        '%',
    };
  }
  const today = computed(() => ((Date.now() - range.value.start) / range.value.span) * 100);
</script>
<template>
  <div class="gantt-scroll">
    <div class="gantt">
      <div class="gantt-heading">
        <b>Actividad / responsable</b>
        <div class="gantt-ticks">
          <span v-for="tick in ticks" :key="tick.toISOString()">{{
            new Intl.DateTimeFormat('es', { day: '2-digit', month: 'short' }).format(tick)
          }}</span>
        </div>
      </div>
      <div
        v-for="task in tasks"
        :key="task.id"
        class="gantt-row"
        @click="$emit('open', task)"
        role="button"
        tabindex="0"
        @keydown.enter="$emit('open', task)"
      >
        <div class="gantt-label">
          <b>{{ task.title }}</b
          ><small>{{ task._labels?.responsible_id }} · {{ dateLabel(task.due_date) }}</small>
        </div>
        <div class="gantt-track">
          <span
            v-if="today >= 0 && today <= 100"
            class="gantt-today"
            :style="{ left: today + '%' }"
          ></span>
          <div class="gantt-bar" :class="task.status" :style="style(task)">
            <span :style="{ width: task.progress + '%' }"></span><b>{{ task.progress }}%</b>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
