<script setup>
  import { computed } from 'vue';
  import { dateLabel } from '../modules';
  import { calendarDay } from '../format';
  const props = defineProps({ tasks: Array });
  defineEmits(['open']);
  const day = 86400000;
  const range = computed(() => {
    const starts = props.tasks.map((t) => calendarDay(t.start_date)),
      ends = props.tasks.map((t) => calendarDay(t.due_date));
    const start = starts.length ? Math.min(...starts) : Date.now();
    const end = ends.length ? Math.max(...ends) : start + 30 * day;
    return { start, end, span: Math.max(day, end - start + day) };
  });
  const ticks = computed(() => {
    const days = Math.max(1, Math.round(range.value.span / day));
    const count = Math.min(7, days);
    return Array.from(
      { length: count },
      (_, i) =>
        new Date(
          range.value.start + (count === 1 ? 0 : Math.round(((days - 1) * i) / (count - 1))) * day,
        ),
    );
  });
  function style(t) {
    return {
      left: ((calendarDay(t.start_date) - range.value.start) / range.value.span) * 100 + '%',
      width:
        (Math.max(day, calendarDay(t.due_date) - calendarDay(t.start_date) + day) /
          range.value.span) *
          100 +
        '%',
    };
  }
  const today = computed(() => {
    const now = new Date();
    const localDay = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    return ((localDay + day / 2 - range.value.start) / range.value.span) * 100;
  });
</script>
<template>
  <div class="gantt-scroll">
    <div class="gantt">
      <div class="gantt-heading">
        <b>Actividad / responsable</b>
        <div class="gantt-ticks">
          <span v-for="tick in ticks" :key="tick.toISOString()">{{
            new Intl.DateTimeFormat('es', {
              day: '2-digit',
              month: 'short',
              timeZone: 'UTC',
            }).format(tick)
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
