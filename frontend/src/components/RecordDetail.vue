<script setup>
  import { ref, computed, watch } from 'vue';
  import { useRouter } from 'vue-router';
  import { api, query } from '../api';
  import { dateLabel, fieldLabel, entityRoutes } from '../modules';
  import TaskProgress from './TaskProgress.vue';
  import StatusBadge from './StatusBadge.vue';
  import { documentState } from '../documentWorkflow';
  const props = defineProps({
    modelValue: Boolean,
    resource: String,
    record: Object,
    meta: Object,
  });
  const emit = defineEmits(['update:modelValue', 'edit', 'action', 'create-related', 'saved']);
  const router = useRouter(),
    related = ref([]),
    loading = ref(false),
    error = ref('');
  const schema = computed(() => props.meta?.[props.resource]);
  const fields = computed(() =>
    Object.entries(props.record || {}).filter(
      ([key]) =>
        !(props.resource === 'documents' && (['project_id', 'preparation_status'].includes(key) ||
          (props.record?.section !== 'recibidos' && ['approval_status', 'intake_format', 'notebook_number'].includes(key)))) &&
        ![
          'id',
          'created_at',
          'updated_at',
          'modified_by',
          'revision',
          '_labels',
          'task_count',
          'password_hash',
          'group_key',
          'participants',
          'member_ids',
          'reported_progress',
          'validated_progress',
          'all_complete',
          'can_edit',
          'can_advance',
          'can_review',
          'can_assign',
          'evidence_count', 'document_count', 'attachments', 'latest_evidence_url', 'latest_evidence_file', 'file',
        ].includes(key) && !(props.resource === 'tasks' && ['project_id', 'axis_id'].includes(key)),
    ),
  );
  const rels = {
    projects: [
      ['tasks', 'project_id'],
      ['milestones', 'project_id'],
      ['documents', 'project_id'],
    ],
    tasks: [
      ['task-assignments', 'task_id'],
      ['task-documents', 'task_id'],
      ['evidence-links', 'task_id'],
      ['closure-approvals', 'task_id'],
      ['tasks', 'parent_id'],
      ['task-dependencies', 'task_id'],
    ],
    documents: [
      ['document-versions', 'document_id'],
      ['task-documents', 'document_id'],
      ['cases', 'document_id'],
      ['evidence-links', 'document_id'],
    ],
    cases: [['case-events', 'case_id']],
    meetings: [
      ['attendees', 'meeting_id'],
      ['agreements', 'meeting_id'],
    ],
    agreements: [['evidence-links', 'agreement_id']],
    evidence: [
      ['evidence-versions', 'evidence_id'],
      ['evidence-links', 'evidence_id'],
    ],
    'evidence-versions': [['evidence-validations', 'evidence_version_id']],
    'service-orders': [['deliverables', 'service_order_id']],
    deliverables: [['deliverable-reviews', 'deliverable_id']],
    indicators: [
      ['indicator-results', 'indicator_id'],
      ['evidence-links', 'indicator_id'],
      ['improvement-plans', 'indicator_id'],
    ],
    'quality-models': [['criteria', 'quality_model_id']],
    criteria: [['indicators', 'criterion_id']],
    users: [['user-roles', 'user_id']],
  };
  const actions = computed(() => {
    const r = props.record || {},
      s = schema.value || {},
      a = [];
    if (props.resource === 'tasks') {
      if (r.can_advance) a.push(['advance', 'Registrar mi avance', 'trending_up']);
      if (r.can_assign) a.push(['participants', 'Agregar participantes', 'group_add']);
      if (r.can_review && r.all_complete && r.status === 'en_revision')
        a.push(['close', 'Validar cierre', 'verified']);
    }
    if (props.resource === 'agreements' && s.can_write)
      a.push(['task', r.task_id ? 'Abrir tarea derivada' : 'Crear tarea', 'add_task']);
    if (props.resource === 'documents' && r.section === 'emitidos' && s.can_write && !r.sent_date && r.preparation_status !== 'anulado')
      a.push(['send', 'Registrar envío', 'send']);
    if (props.resource === 'cases' && s.can_write && !['aprobado', 'atendido'].includes(r.status))
      a.push(['stage', 'Nueva actuación', 'account_tree']);
    if (props.resource === 'evidence-versions' && s.can_validate)
      a.push(['validate', 'Validar versión', 'verified']);
    if (props.resource === 'deliverables' && s.can_validate)
      a.push(['review', 'Registrar revisión', 'fact_check']);
    if (
      ['quality-models', 'criteria'].includes(props.resource) &&
      s.can_validate &&
      r.status !== 'validado'
    )
      a.push(['activate', 'Confirmar revisión', 'verified']);
    if (['user-roles', 'role-permissions'].includes(props.resource) && s.can_write)
      a.push(['revoke', 'Retirar asignación', 'person_remove']);
    return a;
  });
  watch(
    () => [props.modelValue, props.record?.id, props.record?.revision],
    async () => {
      if (!props.modelValue || !props.record) return;
      loading.value = true;
      error.value = '';
      try {
        related.value = await Promise.all(
          (rels[props.resource] || [])
            .filter(([name]) => props.meta[name])
            .map(async ([name, key]) => ({
              name,
              key,
              ...(await api(
                '/' +
                  name +
                  '?' +
                  query({
                    [key]: props.record.id,
                    page_size: 100,
                    scope: props.record.can_review ? 'team' : 'personal',
                  }),
              )),
            })),
        );
      } catch (e) {
        error.value = e.message;
      } finally {
        loading.value = false;
      }
    },
    { immediate: true },
  );
  function label(key) {
    if (props.resource === 'documents') {
      const names = { recipient: 'Destinatario / oficina', axis_id: 'Eje temático',
        responsible_id: props.record?.section === 'emitidos' ? 'Remitente (personal OGC)' : 'Responsable de atención OGC' };
      if (names[key]) return names[key];
    }
    if (key === 'task_id' && props.resource === 'agreements') return 'Tarea derivada';
    return fieldLabel(key, schema.value?.fields.find((field) => field.key === key)?.label);
  }
  function display(key, value) {
    if (props.record?._labels?.[key]) return props.record._labels[key];
    if (typeof value === 'boolean') return value ? 'Sí' : 'No';
    if (value === null || value === '') return '—';
    if (key.endsWith('date') || key === 'date' || key.endsWith('_at')) return dateLabel(value);
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return value;
  }
  function navigate(name, id) {
    if (!entityRoutes[name]) return;
    emit('update:modelValue', false);
    router.push({ path: entityRoutes[name], query: { resource: name, id } });
  }
  function linkTarget(item) {
    const target = Object.keys(item).find(
      (k) =>
        k.endsWith('_id') &&
        ![
          'evidence_id',
          'modified_by',
          'author_id',
          'actor_id',
          'validator_id',
          'approver_id',
        ].includes(k) &&
        item[k],
    );
    return {
      name: {
        task_id: 'tasks',
        project_id: 'projects',
        document_id: 'documents',
        agreement_id: 'agreements',
        meeting_id: 'meetings',
        indicator_id: 'indicators',
      }[target],
      id: item[target],
    };
  }
  function openRelated(name, item) {
    if (name === 'task-documents') {
      return props.resource === 'tasks'
        ? navigate('documents', item.document_id)
        : navigate('tasks', item.task_id);
    }
    if (name === 'evidence-links') {
      if (props.resource !== 'evidence') return navigate('evidence', item.evidence_id);
      const t = linkTarget(item);
      if (t.name) return navigate(t.name, t.id);
    }
    navigate(name, item.id);
  }
  function createRelated(group) {
    const preset = { [group.key]: props.record.id };
    if (group.name === 'tasks') {
      preset.project_id = props.record.project_id || props.record.id;
      preset.responsible_id = props.record.responsible_id;
    }
    if (group.name === 'agreements') {
      preset.project_id = props.record.project_id;
      preset.responsible_id = props.record.responsible_id;
    }
    if (group.name.includes('versions'))
      preset.version = Math.max(0, ...group.items.map((i) => i.version)) + 1;
    emit('create-related', group.name, preset);
  }
</script>
<template>
  <q-dialog :model-value="modelValue" @update:model-value="(v) => emit('update:modelValue', v)"
    ><q-card class="record-detail"
      ><q-card-section class="detail-heading"
        ><div>
          <span class="eyebrow">{{ schema?.label }} · FICHA DEL REGISTRO</span>
          <h2>
            {{ record?.title || record?.name || record?.number || schema?.label }}
          </h2>
          <div class="q-mt-sm">
            <StatusBadge v-if="record?.status" :value="record.status" /><StatusBadge
              v-if="resource === 'documents'"
              :value="documentState(record)"
            />
          </div>
        </div>
        <q-btn flat round icon="close" aria-label="Cerrar detalle" v-close-popup /></q-card-section
      ><q-separator /><q-card-section
        ><div class="detail-actions">
          <q-btn v-if="['documents', 'evidence-versions'].includes(resource) && record?.url" :href="record.url" target="_blank" rel="noopener noreferrer" color="primary" unelevated no-caps icon="description" icon-right="open_in_new" label="Abrir documento" />
          <q-btn
            v-if="
              schema?.can_write &&
              (resource !== 'tasks' || record?.can_edit) &&
              !resource.includes('versions') &&
              !['roles', 'user-roles', 'role-permissions'].includes(resource) &&
              record?.status !== 'cerrada'
            "
            outline
            no-caps
            color="primary"
            label="Editar registro"
            icon="edit"
            @click="emit('edit', record)"
          /><q-btn
            v-for="action in actions"
            :key="action[0]"
            color="primary"
            unelevated
            no-caps
            :label="action[1]"
            :icon="action[2]"
            @click="emit('action', action[0], record)"
          />
        </div>
        <TaskProgress
          v-if="resource === 'tasks' && record?.participants"
          :record="record"
          @saved="emit('saved')"
        />
        <div class="detail-grid">
          <div
            v-for="[key, value] in fields"
            :key="key"
            :class="{
              'full-field': ['description', 'agenda', 'url', 'before', 'after', 'preview'].includes(
                key,
              ),
            }"
          >
            <span class="detail-label">{{ label(key) }}</span
            ><StatusBadge
              v-if="key.endsWith('status') || key === 'priority'"
              :value="String(value || 'pendiente')"
            /><q-linear-progress
              v-else-if="key === 'progress'"
              :value="Number(value) / 100"
              rounded
              size="8px"
            /><a
              v-else-if="['url', 'email_url'].includes(key) && value"
              :href="value"
              target="_blank"
              rel="noopener noreferrer"
              >{{ key === 'email_url' ? 'Abrir correo' : 'Abrir documento' }} <q-icon name="open_in_new"
            /></a>
            <pre v-else-if="typeof value === 'object' && value !== null" class="json-value">{{
              display(key, value)
            }}</pre>
            <p v-else class="detail-value">
              {{ display(key, value) }}<span v-if="key === 'progress'">%</span>
            </p>
          </div>
        </div>
        <div v-if="loading" class="q-my-lg">
          <q-linear-progress indeterminate />
        </div>
        <q-banner v-if="error" class="error-banner" role="alert">{{ error }}</q-banner>
        <section v-for="group in related" :key="group.name" class="related-section">
          <div class="row items-center q-mb-md">
            <h3>
              {{ meta[group.name]?.label }}
              <span class="muted">({{ group.total }})</span>
            </h3>
            <q-space /><q-btn
              v-if="meta[group.name]?.can_write && (resource !== 'tasks' || record?.can_assign)"
              flat
              no-caps
              color="primary"
              icon="add"
              label="Agregar"
              @click="createRelated(group)"
            />
          </div>
          <div v-if="!group.items.length" class="related-empty">No hay registros vinculados.</div>
          <div
            v-for="item in group.items"
            :key="item.id"
            class="related-item"
            role="button"
            tabindex="0"
            @click="openRelated(group.name, item)"
            @keydown.enter="openRelated(group.name, item)"
          >
            <q-icon :name="group.name.includes('evidence') ? 'verified' : 'link'" color="primary" />
            <div>
              <b>{{
                item.title ||
                item.comment ||
                item.note ||
                item._labels.document_id ||
                item._labels.user_id ||
                item._labels.evidence_id ||
                item._labels.role_id ||
                (item.version ? 'Versión ' + item.version : 'Registro vinculado')
              }}</b
              ><small
                >{{ dateLabel(item.created_at)
                }}<span v-if="item.progress !== undefined"> · {{ item.progress }}%</span
                ><span v-if="item.department"> · {{ item.department }}</span
                ><span v-if="item.target !== undefined">
                  · Meta: {{ item.target }} · Resultado: {{ item.result }}</span
                ></small
              >
            </div>
            <StatusBadge v-if="item.status" :value="item.status" /><q-icon name="chevron_right" />
          </div>
          <p v-if="group.total > 100" class="info-note">
            Se muestran los primeros 100 vínculos. Consulta el listado para paginar.
          </p>
        </section>
        <div class="record-audit-footer">
          <span>ID: {{ record?.id }}</span
          ><span v-if="record?.revision"
            >Revisión {{ record?.revision }} · Actualizado {{ dateLabel(record?.updated_at) }} por
            {{ record?._labels?.modified_by || '—' }}</span
          ><span v-else
            >Registrado {{ dateLabel(record?.created_at) }} por
            {{ record?._labels?.actor_id || '—' }}</span
          >
        </div></q-card-section
      ></q-card
    ></q-dialog
  >
</template>
