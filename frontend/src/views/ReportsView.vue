<script setup>
  import { ref, onMounted, computed, watch } from 'vue';
  import { useRouter } from 'vue-router';
  import { useQuasar } from 'quasar';
  import { api, downloadReport, query, can } from '../api';
  import { dateLabel, entityRoutes } from '../modules';
  import FilterBar from '../components/FilterBar.vue';
  const q = useQuasar(),
    router = useRouter(),
    filters = ref({
      year: '',
      month: '',
      responsible_id: '',
      axis_id: '',
      from: '',
      to: '',
      scope: 'personal',
    }),
    lookups = ref({}),
    meta = ref({}),
    alerts = ref([]),
    loading = ref(true),
    error = ref(''),
    busy = ref('');
  const reports = [
    {
      entity: 'tasks',
      title: 'Tareas y avances',
      description: 'Responsables, plazos, prioridad y avance consolidado.',
      icon: 'task_alt',
    },
    {
      entity: 'documents',
      title: 'Registro documental',
      description: 'Documentos emitidos, recibidos y estados de aprobación.',
      icon: 'folder_open',
    },
    {
      entity: 'agreements',
      title: 'Acuerdos y compromisos',
      description: 'Responsables y cumplimiento de los acuerdos de reunión.',
      icon: 'handshake',
    },
    {
      entity: 'deliverables',
      title: 'Entregables OS',
      description: 'Plazos, revisiones, observaciones y conformidades.',
      icon: 'inventory_2',
    },
    {
      entity: 'indicator-results',
      title: 'Resultados de indicadores',
      description: 'Metas y resultados por indicador y periodo.',
      icon: 'insights',
    },
    {
      entity: 'audit',
      title: 'Bitácora de auditoría',
      description: 'Actuaciones registradas y responsables de los cambios.',
      icon: 'history',
    },
  ];
  const available = computed(() => reports.filter((r) => meta.value[r.entity]));
  async function load() {
    loading.value = true;
    error.value = '';
    try {
      [lookups.value, meta.value, alerts.value] = await Promise.all([
        api('/lookups'),
        api('/meta'),
        api('/alerts?' + query({ scope: filters.value.scope })),
      ]);
    } catch (e) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  }
  watch(() => filters.value.scope, load);
  function period(days) {
    const now = new Date();
    const from = new Date(now);
    from.setDate(now.getDate() - days + 1);
    filters.value = {
      ...filters.value,
      from: from.toLocaleDateString('en-CA'),
      to: now.toLocaleDateString('en-CA'),
      year: '',
      month: '',
    };
  }
  async function exportCsv(entity, extra = {}) {
    busy.value = entity;
    try {
      await downloadReport(entity, { ...filters.value, ...extra });
    } catch (e) {
      q.notify({ type: 'negative', message: e.message });
    } finally {
      busy.value = '';
    }
  }
  onMounted(load);
</script>
<template>
  <q-page class="content-page"
    ><div class="page-heading">
      <div>
        <span class="eyebrow">INFORMACIÓN PARA DECIDIR</span>
        <h1>Reportes y alertas<span class="title-dot">.</span></h1>
        <p>Resultados del periodo, compromisos y próximos pasos.</p>
      </div>
      <q-btn outline no-caps color="primary" icon="refresh" label="Actualizar" @click="load" />
    </div>
    <div
      v-if="can(['tasks.supervise', 'tasks.team_read', 'admin.write'])"
      class="segmented q-mb-md"
    >
      <button :class="{ active: filters.scope === 'personal' }" @click="filters.scope = 'personal'">
        Mi espacio
      </button>
      <button :class="{ active: filters.scope === 'team' }" @click="filters.scope = 'team'">
        Equipo
      </button>
    </div>
    <div class="panel reports-filter">
      <div class="row items-center q-mb-md">
        <h2>Define tu periodo</h2>
        <q-space /><q-btn flat no-caps label="Últimos 7 días" @click="period(7)" /><q-btn
          flat
          no-caps
          label="Últimos 30 días"
          @click="period(30)"
        />
      </div>
      <FilterBar v-model="filters" :lookups="lookups" :search="false" expanded />
    </div>
    <q-banner v-if="error" class="error-banner q-my-lg" role="alert">{{ error }}</q-banner>
    <div class="report-grid">
      <section v-for="report in available" :key="report.entity" class="panel report-card">
        <div class="report-icon"><q-icon :name="report.icon" size="26px" /></div>
        <h2>{{ report.title }}</h2>
        <p>{{ report.description }}</p>
        <q-btn
          outline
          color="primary"
          no-caps
          icon="file_download"
          label="Descargar CSV"
          :loading="busy === report.entity"
          @click="exportCsv(report.entity)"
        /><q-btn
          v-if="['tasks', 'agreements'].includes(report.entity)"
          flat
          color="negative"
          no-caps
          label="Solo pendientes vencidos"
          @click="exportCsv(report.entity, { overdue: 'true' })"
        />
      </section>
    </div>
    <section class="panel q-mt-lg">
      <div class="panel-heading">
        <div>
          <h2>Alertas de seguimiento</h2>
          <p>Vencimientos y entregas de los próximos siete días.</p>
        </div>
        <span class="count-pill">{{ alerts.length }}</span>
      </div>
      <q-list separator
        ><q-item
          v-for="alert in alerts"
          :key="alert.id"
          clickable
          @click="
            router.push({
              path: entityRoutes[alert.entity],
              query: { resource: alert.entity, id: alert.id },
            })
          "
          ><q-item-section avatar
            ><q-icon
              :name="alert.overdue ? 'schedule' : 'event'"
              :color="alert.overdue ? 'negative' : 'primary'" /></q-item-section
          ><q-item-section
            ><q-item-label>{{ alert.title }}</q-item-label
            ><q-item-label caption
              >{{ alert.label }} · {{ dateLabel(alert.due_date) }}</q-item-label
            ></q-item-section
          ><q-item-section side
            ><span :class="alert.overdue ? 'text-negative' : 'text-primary'">{{
              alert.overdue ? 'Vencido' : 'Próximo'
            }}</span></q-item-section
          ></q-item
        ></q-list
      >
      <div v-if="!alerts.length && !loading" class="empty-state">
        <q-icon name="notifications_paused" />
        <h3>Sin alertas en este momento</h3>
        <p>Los plazos se revisan cada vez que abres o actualizas el panel.</p>
      </div>
    </section>
    <q-inner-loading :showing="loading"
  /></q-page>
</template>
