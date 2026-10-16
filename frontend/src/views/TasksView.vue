<script setup>
  import SearchSelect from '../components/SearchSelect.vue';
  import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { useQuasar } from 'quasar';
  import { api, can, query } from '../api';
  import { human } from '../format';
  import EntityTable from '../components/EntityTable.vue';
  import TaskAssignmentForm from '../components/TaskAssignmentForm.vue';
  import TaskDetail from '../components/TaskDetail.vue';
  import ActionForm from '../components/ActionForm.vue';
  import TaskAgenda from '../components/TaskAgenda.vue';
  import StatusBadge from '../components/StatusBadge.vue';
  import { dayKey, weekStart, shiftDay } from '../taskAgenda';

  const route = useRoute(),
    q = useQuasar();
  const schema = ref(null),
    lookups = ref({}),
    rows = ref([]),
    loading = ref(true),
    error = ref('');
  const viewScope = (value) =>
    ['assigned', 'team', 'review'].includes(value) ? value : 'received';
  const scope = ref(viewScope(route.query.scope));
  const filters = ref({
    q: route.query.q || '',
    status: '',
    overdue: route.query.overdue || '',
    responsible_id: '',
    from: route.query.from || '',
    to: route.query.to || '',
  });
  const pagination = ref({ page: 1, rowsPerPage: 20, rowsNumber: 0 });
  const formOpen = ref(false),
    editing = ref(null),
    detailOpen = ref(false),
    task = ref(null),
    participantsOpen = ref(false);
  const detailTab = ref('summary'),
    layout = ref('list'),
    week = ref(weekStart());
  const weekLabel = computed(
    () =>
      `${week.value.toLocaleDateString('es-PE', { day: 'numeric', month: 'short' })} – ${shiftDay(week.value, 6).toLocaleDateString('es-PE', { day: 'numeric', month: 'short', year: 'numeric' })}`,
  );
  const teamReader = computed(() => can(['tasks.supervise', 'tasks.team_read', 'admin.write']));
  const reviewer = computed(() => can(['tasks.supervise', 'admin.write']) && can('tasks.validate'));
  const views = computed(() => [
    ['received', 'Mis tareas'],
    ['assigned', 'Tareas que asigné'],
    ...(teamReader.value ? [['team', 'Todas las tareas']] : []),
    ...(reviewer.value ? [['review', 'Evidencias por revisar']] : []),
  ]);
  let sequence = 0,
    active = true;
  async function load() {
    if (!schema.value) return initialize();
    const turn = ++sequence;
    loading.value = true;
    error.value = '';
    try {
      const result = await api(
        '/tasks?' +
          query({
            ...filters.value,
            ...(layout.value === 'agenda'
              ? { from: dayKey(week.value), to: dayKey(shiftDay(week.value, 6)) }
              : {}),
            scope: scope.value === 'review' ? 'team' : scope.value,
            pending_review: scope.value === 'review' ? 'true' : undefined,
            page: pagination.value.page,
            page_size: pagination.value.rowsPerPage,
          }),
      );
      if (!active || turn !== sequence) return;
      rows.value = result.items;
      pagination.value.rowsNumber = result.total;
    } catch (e) {
      if (active && turn === sequence) error.value = e.message;
    } finally {
      if (active && turn === sequence) loading.value = false;
    }
  }
  async function openId(id, tab = 'summary') {
    try {
      const record = await api('/tasks/' + id);
      if (!active) return;
      task.value = record;
      detailTab.value = tab;
      detailOpen.value = true;
    } catch (e) {
      q.notify({ type: 'negative', message: e.message });
    }
  }
  function assign(record = null) {
    editing.value = record;
    formOpen.value = true;
  }
  async function assigned(record) {
    // Show the assignment just created, even when it belongs to someone else.
    if (!editing.value) {
      Object.keys(filters.value).forEach((key) => (filters.value[key] = ''));
      pagination.value.page = 1;
      scope.value = 'assigned';
    }
    await load();
    if (detailOpen.value && task.value?.id === record.id) task.value = record;
    q.notify({
      type: 'positive',
      message: editing.value
        ? 'Tarea actualizada.'
        : 'Tarea asignada. Cada persona seleccionada ya puede verla y añadir evidencias.',
    });
  }
  async function saved(record) {
    if (record?.id === task.value?.id) task.value = record;
    else if (task.value) task.value = await api('/tasks/' + task.value.id);
    await load();
  }
  function request(value) {
    pagination.value = { ...value, rowsNumber: pagination.value.rowsNumber };
    load();
  }
  watch(layout, () => {
    pagination.value.page = 1;
    pagination.value.rowsPerPage = layout.value === 'agenda' ? 100 : 20;
    load();
  });
  watch(week, () => {
    pagination.value.page = 1;
    load();
  });
  watch(
    [filters, scope],
    () => {
      pagination.value.page = 1;
      load();
    },
    { deep: true },
  );
  watch(scope, () => {
    filters.value.responsible_id = '';
  });
  watch(
    () => route.query,
    (params, previous) => {
      if (params.q !== previous.q) filters.value.q = String(params.q || '');
      if (params.overdue !== previous.overdue) filters.value.overdue = String(params.overdue || '');
      if (params.scope !== previous.scope) scope.value = viewScope(params.scope);
      if (params.id && (params.id !== previous.id || params.review !== previous.review))
        openId(params.id, params.review ? 'evidence' : 'summary');
      if (params.from !== previous.from) filters.value.from = String(params.from || '');
      if (params.to !== previous.to) filters.value.to = String(params.to || '');
    },
  );
  watch(teamReader, (allowed) => {
    if (!allowed && scope.value === 'team') scope.value = 'received';
  });
  watch(reviewer, (allowed) => {
    if (!allowed && scope.value === 'review') scope.value = 'received';
  });
  async function initialize() {
    loading.value = true;
    error.value = '';
    try {
      const [meta, choices] = await Promise.all([api('/meta'), api('/lookups')]);
      if (!active) return;
      schema.value = meta.tasks;
      lookups.value = choices;
      await load();
      if (route.query.id) await openId(route.query.id, route.query.review ? 'evidence' : 'summary');
    } catch (e) {
      error.value = e.message;
    } finally {
      if (active) loading.value = false;
    }
  }
  onMounted(initialize);
  onUnmounted(() => {
    active = false;
    sequence++;
  });
</script>
<template>
  <q-page class="content-page tasks-page">
    <div class="page-heading">
      <div>
        <span class="eyebrow">ORGANIZA EL TRABAJO</span>
        <h1>Tareas y responsables<span class="title-dot">.</span></h1>
        <p>Asigna una tarea y sigue sus avances y evidencias.</p>
      </div>
      <q-btn
        v-if="schema?.can_write"
        color="primary"
        unelevated
        no-caps
        icon="add"
        label="Asignar tarea"
        @click="assign()"
      />
    </div>
    <div class="panel module-panel">
      <div class="module-toolbar">
        <div class="segmented" aria-label="Ver tareas">
          <button
            v-for="view in views"
            :key="view[0]"
            :class="{ active: scope === view[0] }"
            :aria-pressed="scope === view[0]"
            @click="scope = view[0]"
          >
            {{ view[1] }}
          </button>
        </div>
        <q-space />
        <q-btn
          flat
          round
          icon="refresh"
          aria-label="Actualizar listado"
          :loading="loading"
          @click="load"
        />
      </div>
      <div class="task-view-options">
        <div class="segmented" aria-label="Presentación de tareas">
          <button
            :class="{ active: layout === 'list' }"
            :aria-pressed="layout === 'list'"
            @click="layout = 'list'"
          >
            <q-icon name="view_list" /> Lista
          </button>
          <button
            :class="{ active: layout === 'agenda' }"
            :aria-pressed="layout === 'agenda'"
            @click="layout = 'agenda'"
          >
            <q-icon name="calendar_month" /> Agenda semanal
          </button>
        </div>
        <div class="task-status-legend" aria-label="Colores de los estados">
          <StatusBadge value="pendiente" /><StatusBadge value="en_progreso" /><StatusBadge
            value="en_revision"
          /><StatusBadge value="cerrada" />
        </div>
      </div>
      <div v-if="layout === 'agenda'" class="agenda-navigation">
        <q-btn
          flat
          round
          icon="chevron_left"
          aria-label="Semana anterior"
          @click="week = shiftDay(week, -7)"
        />
        <strong>{{ weekLabel }}</strong>
        <q-btn
          flat
          round
          icon="chevron_right"
          aria-label="Semana siguiente"
          @click="week = shiftDay(week, 7)"
        />
        <q-btn outline no-caps color="primary" label="Hoy" @click="week = weekStart()" />
      </div>
      <p v-if="scope === 'review'" class="info-note q-mx-lg">
        Estas tareas tienen evidencias pendientes de revisión. Abre una para validar el aporte o
        dejar observaciones.
      </p>
      <div class="module-filters filter-bar">
        <q-input
          v-model="filters.q"
          outlined
          dense
          clearable
          debounce="350"
          placeholder="Buscar tarea…"
          aria-label="Buscar tareas"
          class="filter-search"
          ><template #prepend><q-icon name="search" /></template
        ></q-input>
        <SearchSelect use-input
          v-model="filters.status"
          outlined
          dense
          clearable
          emit-value
          map-options
          label="Estado"
          :options="
            ['pendiente', 'en_progreso', 'en_revision', 'cerrada'].map((value) => ({
              value,
              label: human(value),
            }))
          "
          class="filter-select"
        />
        <SearchSelect use-input
          v-if="scope === 'team' || scope === 'assigned'"
          v-model="filters.responsible_id"
          outlined
          dense
          clearable
          emit-value
          map-options
          label="Persona asignada"
          :options="lookups['task-members'] || []"
          class="filter-select"
        />
        <q-checkbox
          v-model="filters.overdue"
          true-value="true"
          false-value=""
          label="Solo vencidas"
        />
        <q-btn
          v-if="Object.values(filters).some(Boolean)"
          flat
          no-caps
          label="Limpiar filtros"
          @click="Object.keys(filters).forEach((key) => (filters[key] = ''))"
        />
      </div>
      <q-banner v-if="error" class="error-banner q-ma-lg" role="alert"
        >{{ error
        }}<template #action><q-btn flat no-caps label="Reintentar" @click="load" /></template
      ></q-banner>
      <EntityTable
        v-if="layout === 'list'"
        resource="tasks"
        :schema="schema"
        :rows="rows"
        :loading="loading"
        v-model:pagination="pagination"
        @request="request"
        @open="(row) => openId(row.id)"
        @evidence="(row) => openId(row.id, 'evidence')"
        @submit="(row) => openId(row.id, 'submit')"
      />
      <TaskAgenda
        v-else
        :rows="rows"
        :start="week"
        :loading="loading"
        :pagination="pagination"
        @open="(row) => openId(row.id)"
        @evidence="(row) => openId(row.id, 'evidence')"
        @submit="(row) => openId(row.id, 'submit')"
        @page="(page) => request({ ...pagination, page })"
      />
      <p class="info-note q-px-lg q-pb-md">
        {{
          scope === 'received'
            ? 'Abre una tarea para añadir tus avances y evidencias.'
            : 'Abre una tarea para consultar lo que está haciendo el responsable.'
        }}
      </p>
    </div>
    <TaskAssignmentForm v-model="formOpen" :record="editing" :lookups="lookups" @saved="assigned" />
    <TaskDetail
      v-if="task"
      v-model="detailOpen"
      :record="task"
      :initial-tab="detailTab"
      :upload-options="schema?.evidence_upload"
      @edit="assign(task)"
      @participants="participantsOpen = true"
      @saved="saved"
    />
    <ActionForm
      v-if="task"
      v-model="participantsOpen"
      resource="tasks"
      action="participants"
      :record="task"
      :lookups="lookups"
      @saved="saved"
    />
  </q-page>
</template>
