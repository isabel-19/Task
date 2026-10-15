<script setup>
  import { computed } from 'vue';
  import { useQuasar } from 'quasar';
  import StatusBadge from './StatusBadge.vue';
  import TaskEvidenceActions from './TaskEvidenceActions.vue';
  import TaskAssigner from './TaskAssigner.vue';
  import { dayKey } from '../taskAgenda';
  import { dateLabel, fieldLabel } from '../modules';
  import { documentState } from '../documentWorkflow';
  const props = defineProps({
    resource: String,
    schema: Object,
    rows: Array,
    loading: Boolean,
    pagination: Object,
  });
  const emit = defineEmits(['open', 'evidence', 'submit', 'request', 'update:pagination']);
  const q = useQuasar();
  const overdue = (row) =>
    props.resource === 'tasks' && row.due_date < dayKey(new Date()) && row.status !== 'cerrada';
  const tablePagination = computed({
    get: () => props.pagination,
    set: (value) => emit('update:pagination', value),
  });
  const keys = {
    projects: ['title', 'axis_id', 'responsible_id', 'due_date', 'progress', 'status'],
    tasks: ['title', 'participants', 'due_date', 'reported_progress', 'status', 'evidences'],
    documents: [
      'number',
      'title',
      'axis_id',
      'document_type_id',
      'date',
      'document_status',
      'sent_date',
      'url',
    ],
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
          (props.resource === 'tasks' &&
            {
              title: 'Tarea',
              participants: 'Personas asignadas',
              due_date: 'Fecha límite',
              reported_progress: 'Avance reportado',
              evidences: 'Evidencias',
            }[key]) ||
          fieldLabel(key, props.schema?.fields?.find((f) => f.key === key)?.label),
        field: key === 'document_status' ? documentState : key,
        align: 'left',
      }))
      .concat([{ name: 'open', label: '', field: 'id', align: 'right' }]);
  });
  function value(row, key) {
    if (key === 'document_status') return documentState(row);
    if (key === 'participants') return (row.participants || []).map((p) => p.name).join(', ');
    if (row._labels?.[key]) return row._labels[key];
    if (typeof row[key] === 'boolean') return row[key] ? 'Sí' : 'No';
    if (key === 'date' || key.endsWith('_date') || key.endsWith('_at')) return dateLabel(row[key]);
    return row[key] ?? '—';
  }
  function shortValue(row, key) {
    const text = value(row, key);
    if (key === 'participants' && row.participants?.length > 3) {
      return `${row.participants
        .slice(0, 3)
        .map((person) => person.name)
        .join(', ')} y ${row.participants.length - 3} más`;
    }
    return key === 'sha256' && String(text).length > 24
      ? `${String(text).slice(0, 12)}…${String(text).slice(-8)}`
      : text;
  }
  const cardColumns = computed(() =>
    columns.value.filter(
      (column) => !['open', 'title', 'name', 'number', 'status'].includes(column.name),
    ),
  );
  function cardTitle(row) {
    return (
      row.title ||
      row.name ||
      row.number ||
      value(row, columns.value[0]?.name) ||
      props.schema?.label
    );
  }
</script>
<template>
  <div class="collection-caption" role="status">
    <div>
      <q-icon name="folder_open" /><strong>{{ schema?.label }}</strong>
    </div>
    <span>{{ loading ? 'Actualizando…' : `${pagination?.rowsNumber || 0} registros` }}</span>
  </div>
  <q-table
    flat
    :rows="rows"
    :columns="columns"
    row-key="id"
    :loading="loading"
    v-model:pagination="tablePagination"
    :grid="q.screen.lt.sm"
    :rows-per-page-options="[10, 20, 50, 100]"
    @request="(v) => emit('request', v.pagination)"
    class="entity-table"
    @row-click="(_, row) => emit('open', row)"
    ><template #body-cell="p"
      ><q-td :props="p"
        ><q-btn
          v-if="p.col.name === 'open'"
          flat
          :round="resource !== 'tasks'"
          :icon="resource === 'tasks' && p.row.can_advance ? 'attach_file' : 'arrow_forward'"
          size="sm"
          no-caps
          color="primary"
          :label="
            resource === 'tasks'
              ? p.row.can_advance
                ? 'Añadir evidencia'
                : 'Ver tarea'
              : undefined
          "
          :aria-label="
            resource === 'tasks'
              ? p.row.can_advance
                ? 'Añadir evidencia'
                : 'Ver tarea'
              : 'Abrir detalle'
          "
          @click.stop="emit(resource === 'tasks' && p.row.can_advance ? 'submit' : 'open', p.row)"
        /><TaskEvidenceActions
          v-else-if="p.col.name === 'evidences'"
          :record="p.row"
          @open="emit('evidence', p.row)"
        /><StatusBadge
          v-else-if="p.col.name.endsWith('status') || p.col.name === 'priority'"
          :value="p.value"
        />
        <div
          v-else-if="resource === 'tasks' && p.col.name === 'due_date'"
          :class="{ 'task-overdue-date': overdue(p.row) }"
        >
          {{ dateLabel(p.row.due_date) }}<StatusBadge v-if="overdue(p.row)" value="vencida" />
        </div>
        <div
          v-else-if="['progress', 'reported_progress'].includes(p.col.name)"
          class="table-progress"
        >
          <span>{{ p.value }}%</span
          ><q-linear-progress :value="p.value / 100" rounded color="primary" size="4px" />
        </div>
        <q-btn
          v-else-if="p.col.name === 'url' && p.value"
          :href="p.value"
          target="_blank"
          rel="noopener noreferrer"
          color="primary"
          unelevated
          no-caps
          size="sm"
          icon="description"
          icon-right="open_in_new"
          label="Abrir documento"
          @click.stop
        />
        <div v-else-if="resource === 'tasks' && p.col.name === 'title'">
          <span class="table-cell-value table-title">{{ p.row.title }}</span>
          <TaskAssigner :record="p.row" />
        </div>
        <span
          v-else
          class="table-cell-value"
          :title="String(value(p.row, p.col.name))"
          :class="{
            'table-title': ['title', 'number', 'name'].includes(p.col.name),
            'table-fingerprint': p.col.name === 'sha256',
            'document-number': resource === 'documents' && p.col.name === 'number',
          }"
          >{{ shortValue(p.row, p.col.name) }}</span
        ></q-td
      ></template
    ><template #item="p">
      <div class="record-card-container col-12">
        <article class="record-card">
          <header>
            <h3>{{ cardTitle(p.row) }}</h3>
            <StatusBadge v-if="p.row.status" :value="p.row.status" />
          </header>
          <TaskAssigner v-if="resource === 'tasks'" :record="p.row" />
          <dl class="record-card-fields">
            <div v-for="column in cardColumns" :key="column.name">
              <dt>{{ column.label }}</dt>
              <dd>
                <TaskEvidenceActions
                  v-if="column.name === 'evidences'"
                  :record="p.row"
                  @open="emit('evidence', p.row)"
                />
                <StatusBadge
                  v-else-if="column.name.endsWith('status')"
                  :value="value(p.row, column.name)"
                />
                <q-btn
                  v-else-if="column.name === 'url' && p.row.url"
                  :href="p.row.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  color="primary"
                  unelevated
                  no-caps
                  size="sm"
                  icon-right="open_in_new"
                  label="Abrir documento"
                />
                <template v-else-if="['progress', 'reported_progress'].includes(column.name)"
                  >{{ p.row[column.name] }} %<q-linear-progress
                    :value="p.row[column.name] / 100"
                    rounded
                    color="primary"
                /></template>
                <div
                  v-else-if="resource === 'tasks' && column.name === 'due_date'"
                  :class="{ 'task-overdue-date': overdue(p.row) }"
                >
                  {{ dateLabel(p.row.due_date)
                  }}<StatusBadge v-if="overdue(p.row)" value="vencida" />
                </div>
                <template v-else>{{ shortValue(p.row, column.name) }}</template>
              </dd>
            </div>
          </dl>
          <q-btn
            flat
            no-caps
            color="primary"
            icon-right="arrow_forward"
            :label="
              resource === 'tasks'
                ? p.row.can_advance
                  ? 'Añadir evidencia'
                  : 'Ver tarea'
                : 'Ver detalle'
            "
            :aria-label="
              resource === 'tasks'
                ? p.row.can_advance
                  ? 'Añadir evidencia'
                  : 'Ver tarea'
                : 'Abrir detalle'
            "
            @click="emit(resource === 'tasks' && p.row.can_advance ? 'submit' : 'open', p.row)"
          />
        </article>
      </div> </template
    ><template #no-data
      ><div v-if="!loading" class="empty-state table-empty">
        <q-icon name="inbox" />
        <h3>
          {{ resource === 'tasks' ? 'No hay tareas para mostrar' : 'Sin registros para mostrar' }}
        </h3>
        <p>
          {{
            resource === 'tasks'
              ? 'Aquí aparecerán las tareas de la vista seleccionada. Si usaste filtros, prueba cambiarlos.'
              : 'Prueba otros filtros o agrega un nuevo registro.'
          }}
        </p>
      </div></template
    ></q-table
  >
</template>
