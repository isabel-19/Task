<script setup>
  import { computed } from 'vue';
  import StatusBadge from './StatusBadge.vue';
  import { dateLabel, human } from '../modules';
  const props = defineProps({
    resource: String,
    schema: Object,
    rows: Array,
    loading: Boolean,
    pagination: Object,
  });
  const emit = defineEmits(['open', 'request']);
  const keys = {
    projects: ['title', 'axis_id', 'responsible_id', 'due_date', 'progress', 'status'],
    tasks: [
      'title',
      'theme',
      'responsible_id',
      'created_by',
      'participants',
      'due_date',
      'progress',
      'status',
    ],
    documents: ['number', 'title', 'document_type_id', 'section', 'date', 'approval_status'],
    cases: ['number', 'title', 'current_department', 'responsible_id', 'due_date', 'status'],
    meetings: ['title', 'date', 'location', 'responsible_id', 'status'],
    agreements: ['title', 'meeting_id', 'responsible_id', 'due_date', 'status'],
    evidence: ['title', 'category', 'author_id', 'date', 'version', 'validation_status'],
    'evidence-versions': ['evidence_id', 'version', 'url', 'access_confirmed'],
    deliverables: ['title', 'service_order_id', 'responsible_id', 'due_date', 'status'],
    'service-orders': ['number', 'title', 'provider', 'due_date', 'status'],
    indicators: ['title', 'criterion_id', 'responsible_id', 'unit'],
    'indicator-results': ['indicator_id', 'period_id', 'target', 'result'],
    'quality-models': ['title', 'version', 'status'],
    users: ['name', 'email', 'department', 'active'],
    audit: ['created_at', 'entity', 'action', 'actor_id'],
    'task-updates': ['task_id', 'author_id', 'progress', 'comment', 'review_status', 'created_at'],
    'case-events': ['case_id', 'status', 'department', 'note', 'created_at'],
    'evidence-validations': ['evidence_version_id', 'status', 'validator_id', 'note'],
    'closure-approvals': ['task_id', 'approver_id', 'evidence_version_id', 'justification'],
    'deliverable-reviews': ['deliverable_id', 'status', 'reviewer_id', 'note'],
  };
  const columns = computed(() => {
    const fields =
      keys[props.resource] || props.schema?.fields?.slice(0, 5).map((f) => f.key) || [];
    return fields
      .map((key) => ({
        name: key,
        label:
          props.schema?.fields?.find((f) => f.key === key)?.label ||
          {
            progress: 'Avance',
            status: 'Estado',
            approval_status: 'Aprobación',
            validation_status: 'Validación',
            author_id: 'Autor',
            created_by: 'Asignada por',
            participants: 'Participantes',
            theme: 'Temática / eje',
            review_status: 'Revisión del jefe',
            created_at: 'Fecha',
            action: 'Acción',
            actor_id: 'Usuario',
          }[key] ||
          human(key),
        field: key,
        align: 'left',
      }))
      .concat([{ name: 'open', label: '', field: 'id', align: 'right' }]);
  });
  function value(row, key) {
    if (key === 'participants') return (row.participants || []).map((p) => p.name).join(', ');
    if (row._labels?.[key]) return row._labels[key];
    if (typeof row[key] === 'boolean') return row[key] ? 'Sí' : 'No';
    if (key === 'date' || key.endsWith('_date') || key.endsWith('_at')) return dateLabel(row[key]);
    return row[key] ?? '—';
  }
</script>
<template>
  <q-table
    flat
    :rows="rows"
    :columns="columns"
    row-key="id"
    :loading="loading"
    :pagination="pagination"
    :rows-per-page-options="[10, 20, 50, 100]"
    @request="(v) => emit('request', v.pagination)"
    class="entity-table"
    @row-click="(_, row) => emit('open', row)"
    ><template #body-cell="p"
      ><q-td :props="p"
        ><q-btn
          v-if="p.col.name === 'open'"
          flat
          round
          icon="arrow_forward"
          size="sm"
          aria-label="Abrir detalle"
          @click.stop="emit('open', p.row)"
        /><StatusBadge
          v-else-if="p.col.name.endsWith('status') || p.col.name === 'priority'"
          :value="p.value"
        />
        <div v-else-if="p.col.name === 'progress'" class="table-progress">
          <span>{{ p.value }}%</span
          ><q-linear-progress :value="p.value / 100" rounded color="primary" size="4px" />
        </div>
        <span v-else :class="{ 'table-title': ['title', 'number', 'name'].includes(p.col.name) }">{{
          value(p.row, p.col.name)
        }}</span></q-td
      ></template
    ><template #no-data
      ><div class="empty-state table-empty">
        <q-icon name="inbox" />
        <h3>Sin registros para mostrar</h3>
        <p>Prueba otros filtros o agrega un nuevo registro.</p>
      </div></template
    ></q-table
  >
</template>
