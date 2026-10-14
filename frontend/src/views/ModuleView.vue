<script setup>
  import { ref, computed, watch, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useQuasar } from 'quasar';
  import { api, query, downloadReport, can, session } from '../api';
  import { entityRoutes, dateLabel, human } from '../modules';
  import FilterBar from '../components/FilterBar.vue';
  import EntityTable from '../components/EntityTable.vue';
  import RecordForm from '../components/RecordForm.vue';
  import RecordDetail from '../components/RecordDetail.vue';
  import ActionForm from '../components/ActionForm.vue';
  import StatusBadge from '../components/StatusBadge.vue';
  import GanttChart from '../components/GanttChart.vue';
  import ImportPanel from '../components/ImportPanel.vue';
  import ParticipantDirectory from '../components/ParticipantDirectory.vue';
  const route = useRoute(),
    router = useRouter(),
    q = useQuasar();
  const meta = ref({}),
    lookups = ref({}),
    selected = ref(route.query.resource || route.meta.resources[0]),
    rows = ref([]),
    ganttTasks = ref([]),
    loading = ref(false),
    error = ref(''),
    expanded = ref(false),
    mode = ref('list'),
    scope = ref(route.query.scope || 'personal');
  const filters = ref({
    q: route.query.q || '',
    overdue: route.query.overdue || '',
    approval_status: route.query.approval_status || '',
    from: route.query.from || '',
    to: route.query.to || '',
    axis_id: '',
    responsible_id: '',
    year: '',
    status: '',
    section: '',
    document_type_id: '',
  });
  const pagination = ref({ page: 1, rowsPerPage: 20, rowsNumber: 0 });
  const detailOpen = ref(false),
    detailRecord = ref(null),
    detailResource = ref(''),
    formOpen = ref(false),
    formResource = ref(''),
    formRecord = ref(null),
    preset = ref({}),
    actionOpen = ref(false),
    action = ref(''),
    actionRecord = ref(null),
    actionResource = ref(''),
    importOpen = ref(false),
    participantsOpen = ref(false);
  const currentSchema = computed(() => meta.value[selected.value]),
    tabs = computed(() => route.meta.resources.filter((r) => meta.value[r]));
  const states = computed(
    () =>
      ({
        tasks: ['pendiente', 'en_progreso', 'en_revision', 'cerrada'],
        cases: [
          'elaboracion',
          'revision',
          'firma',
          'derivacion',
          'observado',
          'subsanacion',
          'aprobado',
          'atendido',
        ],
        agreements: ['pendiente', 'en_progreso', 'cumplido'],
        deliverables: ['pendiente', 'en_revision', 'observado', 'conforme'],
        evidence: [],
        projects: ['planificado', 'en_progreso', 'en_pausa', 'finalizado'],
      })[selected.value] ||
      currentSchema.value?.fields.find((f) => f.key === 'status')?.options ||
      [],
  );
  let sequence = 0;
  async function refreshMeta() {
    const [schema, options] = await Promise.all([api('/meta'), api('/lookups')]);
    meta.value = schema;
    lookups.value = options;
    if (!meta.value[selected.value]) selected.value = tabs.value[0];
  }
  async function load() {
    if (!currentSchema.value) return;
    const turn = ++sequence;
    loading.value = true;
    error.value = '';
    try {
      const result = await api(
        '/' +
          selected.value +
          '?' +
          query({
            ...filters.value,
            scope: scope.value,
            page: pagination.value.page,
            page_size: pagination.value.rowsPerPage,
          }),
      );
      if (turn !== sequence) return;
      rows.value = result.items;
      pagination.value.rowsNumber = result.total;
      if (mode.value === 'gantt') {
        const tasks = await api(
          '/tasks?' + query({ ...filters.value, scope: scope.value, page_size: 100 }),
        );
        if (turn === sequence) ganttTasks.value = tasks.items;
      }
    } catch (e) {
      if (turn === sequence) error.value = e.message;
    } finally {
      if (turn === sequence) loading.value = false;
    }
  }
  async function openId(resource, id) {
    try {
      detailResource.value = resource;
      detailRecord.value = await api('/' + resource + '/' + id);
      detailOpen.value = true;
    } catch (e) {
      q.notify({ type: 'negative', message: e.message });
    }
  }
  function open(row) {
    detailResource.value = selected.value;
    detailRecord.value = row;
    detailOpen.value = true;
  }
  function newRecord(resource = selected.value, values = {}) {
    formResource.value = resource;
    formRecord.value = null;
    preset.value = values;
    formOpen.value = true;
  }
  function edit(record) {
    formResource.value = detailResource.value;
    formRecord.value = record;
    preset.value = {};
    formOpen.value = true;
  }
  function act(name, record) {
    if (name === 'task' && record.task_id) {
      detailOpen.value = false;
      router.push({ path: '/tareas', query: { id: record.task_id } });
      return;
    }
    actionResource.value = detailResource.value;
    actionRecord.value = record;
    action.value = name;
    actionOpen.value = true;
  }
  async function saved() {
    try {
      await refreshMeta();
      await load();
      if (detailOpen.value && detailRecord.value)
        await openId(detailResource.value, detailRecord.value.id);
      q.notify({ type: 'positive', message: 'Registro guardado y trazabilidad actualizada.' });
    } catch (e) {
      q.notify({ type: 'negative', message: e.message });
    }
  }
  function request(p) {
    pagination.value = { ...p, rowsNumber: pagination.value.rowsNumber };
    load();
  }
  async function exportCsv() {
    try {
      await downloadReport(selected.value, {
        ...filters.value,
        scope: scope.value,
      });
    } catch (e) {
      q.notify({ type: 'negative', message: e.message });
    }
  }
  watch(
    [filters, scope, mode],
    () => {
      pagination.value.page = 1;
      load();
    },
    { deep: true },
  );
  watch(selected, () => {
    filters.value.status = '';
    filters.value.section = '';
    filters.value.document_type_id = '';
    mode.value = 'list';
    pagination.value.page = 1;
    load();
  });
  watch(
    () => route.query,
    async (params) => {
      if (params.scope) scope.value = params.scope;
      if (params.resource && tabs.value.includes(params.resource)) selected.value = params.resource;
      if (params.id) await openId(params.resource || selected.value, params.id);
    },
  );
  onMounted(async () => {
    try {
      await refreshMeta();
      await load();
      if (route.query.id) await openId(route.query.resource || selected.value, route.query.id);
    } catch (e) {
      error.value = e.message;
    }
  });
</script>
<template>
  <q-page class="content-page module-page"
    ><div class="page-heading">
      <div>
        <span class="eyebrow">GESTIÓN Y SEGUIMIENTO</span>
        <h1>{{ route.meta.label }}<span class="title-dot">.</span></h1>
        <p>{{ route.meta.subtitle }}</p>
      </div>
      <q-btn
        v-if="currentSchema?.can_write"
        color="primary"
        unelevated
        no-caps
        icon="add"
        label="Nuevo registro"
        @click="newRecord()"
      />
    </div>
    <div v-if="route.path === '/tareas'" class="row items-center q-mb-md">
      <q-btn
        outline
        no-caps
        color="primary"
        icon="groups"
        label="Participantes del equipo"
        @click="participantsOpen = true"
      />
      <span v-if="session.realParticipants" class="q-ml-md muted"
        >{{ session.importedParticipants }} nombres del Excel disponibles para asignar tareas</span
      >
    </div>
    <p v-if="route.path === '/tramites'" class="module-note">
      <q-icon name="info_outline" /> Un documento remitido puede seguir pendiente de aprobación.
      Cada actuación conserva la dependencia externa y su historial.
    </p>
    <p v-if="route.path === '/indicadores'" class="module-note">
      <q-icon name="verified_user" /> Revisa la versión y aplicabilidad de modelos y criterios antes
      de activarlos. Los registros de prueba carecen de vigencia normativa.
    </p>
    <p v-if="route.path === '/servicios'" class="module-note">
      <q-icon name="info_outline" /> Seguimiento interno de entregables. La conformidad requiere un
      documento de presentación.
    </p>
    <div class="panel module-panel">
      <div class="module-tabs">
        <button
          v-for="tab in tabs"
          :key="tab"
          :class="{ active: selected === tab }"
          @click="selected = tab"
        >
          {{ meta[tab].label }}</button
        ><q-space /><q-btn
          v-if="route.path === '/administracion' && can('admin.write') && session.importsEnabled"
          flat
          no-caps
          icon="upload_file"
          label="Importar"
          color="primary"
          @click="importOpen = true"
        />
      </div>
      <div class="module-toolbar">
        <div v-if="selected === 'tasks'" class="segmented">
          <button
            v-for="view in [
              ['personal', 'Mi espacio'],
              ['received', 'Me asignaron'],
              ['assigned', 'Asigné'],
              ['joint', 'En conjunto'],
            ]"
            :key="view[0]"
            :class="{ active: scope === view[0] }"
            @click="scope = view[0]"
          >
            {{ view[1] }}
          </button>
          <button
            v-if="can(['tasks.supervise', 'tasks.team_read', 'admin.write'])"
            :class="{ active: scope === 'team' }"
            @click="scope = 'team'"
          >
            Equipo
          </button>
        </div>
        <div v-if="selected === 'documents'" class="document-sections">
          <button
            v-for="section in [
              ['', 'Todos'],
              ['emitidos', 'Emitidos'],
              ['recibidos', 'Recibidos'],
              ['normativos', 'Normativos / técnicos'],
              ['archivo', 'Archivo digital'],
            ]"
            :key="section[0]"
            :class="{ active: filters.section === section[0] }"
            @click="filters.section = section[0]"
          >
            {{ section[1] }}
          </button>
        </div>
        <q-space />
        <div v-if="selected === 'tasks' || selected === 'projects'" class="view-toggle">
          <q-btn
            flat
            round
            icon="view_list"
            aria-label="Vista de lista"
            :color="mode === 'list' ? 'primary' : 'grey'"
            @click="mode = 'list'"
          /><q-btn
            v-if="selected === 'tasks'"
            flat
            round
            icon="view_kanban"
            aria-label="Vista Kanban"
            :color="mode === 'kanban' ? 'primary' : 'grey'"
            @click="
              mode = 'kanban';
              pagination.rowsPerPage = 100;
              load();
            "
          /><q-btn
            v-if="selected === 'projects'"
            flat
            round
            icon="date_range"
            aria-label="Vista Gantt"
            :color="mode === 'gantt' ? 'primary' : 'grey'"
            @click="mode = 'gantt'"
          />
        </div>
        <q-btn flat no-caps icon="file_download" label="Exportar" @click="exportCsv" /><q-btn
          flat
          round
          icon="refresh"
          aria-label="Actualizar listado"
          @click="load"
        />
      </div>
      <div class="module-filters">
        <FilterBar v-model="filters" :lookups="lookups" :expanded="expanded" />
        <div class="filter-bar q-mt-sm">
          <q-select
            v-if="states.length"
            v-model="filters.status"
            outlined
            dense
            clearable
            label="Todos los estados"
            :options="states"
            class="filter-select"
          /><q-select
            v-if="selected === 'documents'"
            v-model="filters.document_type_id"
            outlined
            dense
            clearable
            emit-value
            map-options
            label="Tipo documental"
            :options="lookups['document-types'] || []"
            class="filter-select"
          /><q-checkbox
            v-if="['tasks', 'deliverables', 'cases', 'agreements'].includes(selected)"
            v-model="filters.overdue"
            true-value="true"
            false-value=""
            label="Solo vencidos"
          /><q-space /><q-btn
            flat
            no-caps
            icon="tune"
            :label="expanded ? 'Menos filtros' : 'Más filtros'"
            @click="expanded = !expanded"
          /><q-btn
            v-if="Object.values(filters).some(Boolean)"
            flat
            no-caps
            label="Limpiar"
            @click="Object.keys(filters).forEach((k) => (filters[k] = ''))"
          />
        </div>
      </div>
      <q-banner v-if="error" class="error-banner q-ma-lg" role="alert"
        >{{ error
        }}<template #action
          ><q-btn flat no-caps label="Reintentar" @click="load" /></template></q-banner
      ><EntityTable
        v-if="mode === 'list'"
        :resource="selected"
        :schema="currentSchema"
        :rows="rows"
        :loading="loading"
        :pagination="pagination"
        @open="open"
        @request="request"
      />
      <div v-if="mode === 'kanban'" class="kanban-board">
        <div
          v-for="status in ['pendiente', 'en_progreso', 'en_revision', 'cerrada']"
          :key="status"
          class="kanban-column"
        >
          <div class="kanban-heading">
            <StatusBadge :value="status" /><b>{{
              rows.filter((r) => r.status === status).length
            }}</b>
          </div>
          <button
            v-for="task in rows.filter((r) => r.status === status)"
            :key="task.id"
            class="kanban-card"
            @click="open(task)"
          >
            <span class="kanban-project">{{ task._labels.project_id }}</span>
            <h3>{{ task.title }}</h3>
            <StatusBadge :value="task.priority" /><q-linear-progress
              :value="task.progress / 100"
              rounded
              color="primary"
              size="4px"
              class="q-mt-md"
            />
            <div class="kanban-foot">
              <span>{{ task._labels.responsible_id }}</span
              ><span>{{ dateLabel(task.due_date) }}</span>
            </div>
          </button>
          <p v-if="!rows.some((r) => r.status === status)" class="kanban-empty">
            Sin tareas en este estado
          </p>
        </div>
      </div>
      <div v-if="mode === 'gantt'">
        <p class="info-note q-ma-lg">
          Cronograma de hasta 100 actividades filtradas. Abre una barra para consultar responsables,
          dependencias, hitos y avances.
        </p>
        <GanttChart
          :tasks="ganttTasks"
          @open="(task) => router.push({ path: '/tareas', query: { id: task.id } })"
        />
        <div v-if="!ganttTasks.length" class="empty-state">
          <q-icon name="date_range" />
          <h3>Sin actividades para el cronograma</h3>
          <p>Crea tareas vinculadas a un proyecto.</p>
        </div>
      </div>
      <div v-if="mode === 'kanban'" class="row items-center justify-between q-pa-md">
        <span>{{ pagination.rowsNumber }} tareas · Página {{ pagination.page }}</span
        ><q-pagination
          v-model="pagination.page"
          :max="Math.max(1, Math.ceil(pagination.rowsNumber / pagination.rowsPerPage))"
          @update:model-value="load"
        />
      </div>
    </div>
    <ParticipantDirectory
      v-model="participantsOpen"
      @assign="(id) => newRecord('tasks', { responsible_id: id })" />
    <RecordForm
      v-model="formOpen"
      :resource="formResource"
      :schema="meta[formResource]"
      :record="formRecord"
      :preset="preset"
      :lookups="lookups"
      @saved="saved" /><RecordDetail
      v-model="detailOpen"
      :resource="detailResource"
      :record="detailRecord"
      :meta="meta"
      @edit="edit"
      @action="act"
      @create-related="newRecord"
      @saved="saved" /><ActionForm
      v-model="actionOpen"
      :resource="actionResource"
      :record="actionRecord"
      :action="action"
      :lookups="lookups"
      @saved="saved" /><q-dialog v-model="importOpen"
      ><q-card class="import-dialog"
        ><q-card-section class="row items-center"
          ><h2>Importación con previsualización</h2>
          <q-space /><q-btn
            flat
            round
            icon="close"
            aria-label="Cerrar importación"
            v-close-popup /></q-card-section
        ><ImportPanel :meta="meta" :lookups="lookups" @imported="saved" /></q-card></q-dialog
  ></q-page>
</template>
