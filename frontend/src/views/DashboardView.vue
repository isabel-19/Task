<script setup>
  import { ref, watch, onMounted, computed } from 'vue';
  import { useRouter } from 'vue-router';
  import { api, query, session, can } from '../api';
  import FilterBar from '../components/FilterBar.vue';
  import StatusBadge from '../components/StatusBadge.vue';
  import RouteMotif from '../components/RouteMotif.vue';
  import { dateLabel, entityRoutes, human } from '../modules';
  const router = useRouter(),
    data = ref(null),
    lookups = ref({}),
    loading = ref(true),
    error = ref('');
  const filters = ref({ year: '', axis_id: '', responsible_id: '', scope: 'personal' }),
    expanded = ref(false);
  let sequence = 0;
  async function load() {
    const turn = ++sequence;
    loading.value = true;
    error.value = '';
    try {
      const result = await api('/dashboard?' + query(filters.value));
      if (turn === sequence) data.value = result;
    } catch (e) {
      if (turn === sequence) error.value = e.message;
    } finally {
      if (turn === sequence) loading.value = false;
    }
  }
  onMounted(async () => {
    try {
      lookups.value = await api('/lookups');
    } catch (e) {
      error.value = e.message;
    }
    load();
  });
  watch(filters, load, { deep: true });
  const cards = computed(() =>
    data.value
      ? [
          {
            label: 'Tareas pendientes',
            value: data.value.pending,
            note: 'Compromisos por completar',
            icon: 'checklist',
            color: 'teal',
            action: { path: '/tareas' },
          },
          {
            label: 'Tareas vencidas',
            value: data.value.overdue,
            note: 'Requieren tu atención',
            icon: 'schedule',
            color: 'coral',
            action: { path: '/tareas', query: { overdue: 'true' } },
          },
          {
            label: 'Entregas esta semana',
            value: data.value.upcoming,
            note: 'En los próximos 7 días',
            icon: 'event_note',
            color: 'gold',
            action: {
              path: '/tareas',
              query: {
                from: new Date().toLocaleDateString('en-CA'),
                to: new Date(Date.now() + 7 * 86400000).toLocaleDateString('en-CA'),
              },
            },
          },
          {
            label: 'Documentos por atender',
            value: data.value.pending_documents,
            note: 'Recibidos pendientes de atención',
            icon: 'description',
            color: 'violet',
            action: { path: '/registro', query: { section: 'recibidos', approval_status: 'pendiente', attended: 'false' } },
          },
        ]
      : [],
  );
  function open(entity, id) {
    router.push({ path: entityRoutes[entity], query: { resource: entity, id } });
  }
  function openCard(card) {
    router.push({ ...card.action, query: { ...card.action.query, scope: filters.value.scope } });
  }
  const today = new Intl.DateTimeFormat('es-PE', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date());
</script>
<template>
  <q-page class="content-page dashboard-page">
    <div class="page-heading dashboard-heading">
      <div>
        <span class="eyebrow">PANORAMA GENERAL</span>
        <h1>Panel de seguimiento<span class="title-dot">.</span></h1>
        <p>Hola, {{ session.user?.name.split(' ')[0] }}. Sigue tus compromisos y el avance de tu equipo.</p>
      </div>
      <div class="dashboard-heading-aside">
        <div class="date-pill"><q-icon name="calendar_today" size="17px" />{{ today }}</div>
        <RouteMotif />
      </div>
    </div>
    <div
      v-if="can(['tasks.supervise', 'tasks.team_read', 'admin.write'])"
      class="segmented q-mb-md"
    >
      <button :class="{ active: filters.scope === 'personal' }" :aria-pressed="filters.scope === 'personal'" @click="filters.scope = 'personal'">
        Mi espacio
      </button>
      <button :class="{ active: filters.scope === 'team' }" :aria-pressed="filters.scope === 'team'" @click="filters.scope = 'team'">
        Equipo
      </button>
    </div>
    <div class="filter-panel">
      <FilterBar v-model="filters" :lookups="lookups" :search="false" :expanded="expanded" /><q-btn
        flat
        no-caps
        :icon="expanded ? 'filter_list_off' : 'tune'"
        :label="expanded ? 'Menos filtros' : 'Más filtros'"
        @click="expanded = !expanded"
      />
    </div>
    <q-banner v-if="error" class="error-banner q-mb-lg" role="alert"
      >{{ error
      }}<template #action><q-btn flat label="Reintentar" no-caps @click="load" /></template
    ></q-banner>
    <div v-if="loading && !data" class="metrics-grid">
      <q-skeleton v-for="n in 4" :key="n" height="160px" />
    </div>
    <template v-if="data">
      <div class="metrics-grid">
        <button v-for="card in cards" :key="card.label" class="metric-card" :class="'metric-' + card.color" @click="openCard(card)">
          <div class="metric-top">
            <span>{{ card.label }}</span>
            <div class="metric-icon" :class="card.color">
              <q-icon :name="card.icon" size="22px" />
            </div>
          </div>
          <strong>{{ card.value.toString().padStart(2, '0') }}</strong>
          <div class="metric-bottom">
            <span>{{ card.note }}</span
            ><q-icon name="north_east" size="16px" />
          </div>
        </button>
      </div>
      <div class="dashboard-main-grid">
        <section class="panel projects-panel">
          <div class="panel-heading">
            <div>
              <h2>Proyectos en marcha</h2>
              <p>Una vista de la ruta que estamos construyendo.</p>
            </div>
            <q-btn
              flat
              no-caps
              color="primary"
              label="Ver roadmap"
              icon-right="arrow_forward"
              to="/proyectos"
            />
          </div>
          <div v-if="!data.projects.length" class="empty-state">
            <q-icon name="route" />
            <h3>Aún no hay proyectos</h3>
            <p>Crea tu primer proyecto para empezar el seguimiento.</p>
          </div>
          <div
            v-for="(project, i) in data.projects"
            :key="project.id"
            class="project-row"
            @click="open('projects', project.id)"
            role="button"
            tabindex="0"
            @keydown.enter="open('projects', project.id)"
          >
            <span class="project-monogram" :class="['teal', 'violet', 'gold'][i % 3]">{{
              String(i + 1).padStart(2, '0')
            }}</span>
            <div class="project-info">
              <h3>{{ project.title }}</h3>
              <span>{{ project._labels.axis_id }} · {{ project.task_count }} tareas</span
              ><q-linear-progress
                :value="project.progress / 100"
                color="primary"
                track-color="grey-3"
                rounded
                size="5px"
              />
            </div>
            <div class="project-meta">
              <b>{{ project.progress }}<small>%</small></b
              ><span>{{ dateLabel(project.due_date) }}</span>
            </div>
            <q-icon name="chevron_right" color="grey-5" size="21px" />
          </div>
        </section>
        <section class="progress-card">
          <span class="eyebrow light">AVANCE DEL PERIODO</span>
          <h2>Cada paso cuenta.</h2>
          <p>Progreso consolidado de las tareas filtradas.</p>
          <div class="progress-ring" :style="{ '--progress': data.progress + '%' }">
            <div>
              <strong>{{ data.progress }}<span>%</span></strong
              ><small>avance general</small>
            </div>
          </div>
          <div class="progress-foot">
            <span
              ><b>{{ data.closed }}</b> tareas cerradas</span
            ><span
              ><b>{{ data.task_count }}</b> tareas registradas</span
            >
          </div>
          <router-link to="/reportes"
            >Explorar resultados <q-icon name="arrow_forward"
          /></router-link>
        </section>
      </div>
      <div class="dashboard-secondary-grid">
        <section class="panel deadlines-panel">
          <div class="panel-heading">
            <div>
              <h2>Próximas entregas</h2>
              <p>La agenda de los próximos siete días.</p>
            </div>
            <span class="count-pill">{{ data.upcoming }}</span>
          </div>
          <div v-if="!data.upcoming_tasks.length" class="empty-state compact">
            <q-icon name="event_available" />
            <p>No hay entregas en los próximos 7 días.</p>
          </div>
          <div
            v-for="task in data.upcoming_tasks"
            :key="task.id"
            class="deadline-row"
            role="button"
            tabindex="0"
            @click="open('tasks', task.id)"
            @keydown.enter="open('tasks', task.id)"
          >
            <div class="deadline-date">
              <b>{{ new Date(task.due_date + 'T12:00:00').getDate() }}</b
              ><span>{{
                new Intl.DateTimeFormat('es', { month: 'short' })
                  .format(new Date(task.due_date + 'T12:00:00'))
                  .replace('.', '')
              }}</span>
            </div>
            <div class="deadline-text">
              <h3>{{ task.title }}</h3>
              <span>{{ task._labels.responsible_id }}</span>
            </div>
            <StatusBadge :value="task.status" />
          </div>
        </section>
        <section class="panel team-panel">
          <div class="panel-heading">
            <div>
              <h2>Avance por responsable</h2>
              <p>Un equipo, una ruta compartida.</p>
            </div>
            <q-icon name="groups" size="24px" color="grey-5" />
          </div>
          <div v-if="!data.by_person.length" class="empty-state compact">
            <p>No hay tareas en este periodo.</p>
          </div>
          <div v-for="(person, i) in data.by_person" :key="person.id" class="person-row">
            <q-avatar size="36px" :class="['teal', 'violet', 'gold'][i % 3]">{{
              person.name[0]
            }}</q-avatar>
            <div>
              <b>{{ person.name }}</b
              ><span>{{ person.count }} tareas asignadas</span>
            </div>
            <div class="person-progress">
              <b>{{ person.progress }}%</b
              ><q-linear-progress
                :value="person.progress / 100"
                color="primary"
                track-color="grey-3"
                rounded
                size="4px"
              />
            </div>
          </div>
          <div class="agreement-callout">
            <q-icon name="handshake" />
            <div>
              <b>{{ data.pending_agreements }} acuerdos pendientes</b>
              <p>Dales seguimiento en tu próxima reunión.</p>
            </div>
            <q-btn
              flat
              round
              icon="arrow_forward"
              aria-label="Ver acuerdos pendientes"
              :to="{ path: '/reuniones', query: { resource: 'agreements' } }"
            />
          </div>
        </section>
      </div>
      <div class="dashboard-secondary-grid q-mt-lg">
        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>Seguimiento por eje</h2>
              <p>Avance de las prioridades del periodo.</p>
            </div>
          </div>
          <div v-for="axis in data.by_axis" :key="axis.id" class="axis-row">
            <div class="row justify-between">
              <b>{{ axis.name }}</b
              ><span>{{ axis.progress }}%</span>
            </div>
            <q-linear-progress
              :value="axis.progress / 100"
              :style="{ color: axis.color }"
              track-color="grey-3"
              rounded
              size="7px"
            /><span class="muted">{{ axis.count }} tareas</span>
          </div>
          <p v-if="!data.by_axis.length" class="empty-state compact">
            Sin tareas para los filtros elegidos.
          </p>
        </section>
        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>Necesitan atención</h2>
              <p>Compromisos fuera de plazo.</p>
            </div>
            <q-icon name="priority_high" color="negative" />
          </div>
          <div
            v-for="task in data.overdue_tasks"
            :key="task.id"
            class="attention-row"
            role="button"
            tabindex="0"
            @click="open('tasks', task.id)"
            @keydown.enter="open('tasks', task.id)"
          >
            <q-icon name="schedule" color="negative" />
            <div>
              <b>{{ task.title }}</b
              ><span>{{ task._labels.responsible_id }} · {{ dateLabel(task.due_date) }}</span>
            </div>
            <q-icon name="chevron_right" />
          </div>
          <div v-if="!data.overdue_tasks.length" class="empty-state compact">
            <q-icon name="check_circle_outline" />
            <p>No hay tareas vencidas.</p>
          </div>
        </section>
      </div> </template
    ><q-inner-loading :showing="loading && !!data" />
  </q-page>
</template>
