<script setup>
  import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useQuasar } from 'quasar';
  import { modules, entityRoutes, dateLabel } from './modules';
  import { session, can, logout, api } from './api';
  const route = useRoute(),
    router = useRouter(),
    q = useQuasar();
  const drawer = ref(true),
    alertsOpen = ref(false),
    alerts = ref([]),
    search = ref(''),
    loadingAlerts = ref(false);
  const available = computed(() => modules.filter((m) => can(m.permission)));
  const pendingReviewCount = computed(
    () => alerts.value.filter((alert) => alert.kind === 'task_review').length,
  );
  let alertTimer,
    alertSequence = 0,
    knownReviewIds = null,
    knownNoticeIds = null;
  function noticeAlert(notice) {
    return {
      kind: 'notification',
      notice_id: notice.id,
      entity: notice.entity,
      id: notice.record_id,
      title: notice.title,
      message: notice.message,
      label: 'Reunión',
      overdue: false,
    };
  }
  async function openAlert(alert) {
    if (alert.kind === 'notification') {
      // Opening a notice marks it as read so it leaves the bell.
      try {
        await api('/notifications/' + alert.notice_id + '/read', { method: 'POST' });
        alerts.value = alerts.value.filter((item) => item !== alert);
      } catch (e) {
        q.notify({ type: 'negative', message: e.message });
      }
    }
    router.push({
      path: entityRoutes[alert.entity],
      query:
        alert.kind === 'task_review'
          ? { id: alert.task_id, scope: 'review', review: alert.id }
          : { resource: alert.entity, id: alert.id },
    });
    alertsOpen.value = false;
  }
  const initials = computed(() =>
    session.user?.name
      .split(' ')
      .map((w) => w[0])
      .slice(0, 2)
      .join(''),
  );
  async function loadAlerts() {
    if (!session.user) return;
    const userId = session.user.id,
      turn = ++alertSequence;
    loadingAlerts.value = true;
    try {
      const [result, notices] = await Promise.all([
        can('reports.read') ? api('/alerts') : [],
        api('/notifications'),
      ]);
      if (turn !== alertSequence || session.user?.id !== userId) return;
      alerts.value = [...notices.map(noticeAlert), ...result];
      const freshNotices = notices.filter((notice) => !knownNoticeIds?.has(notice.id));
      if (freshNotices.length && knownNoticeIds !== null)
        q.notify({
          type: 'info',
          message:
            freshNotices.length === 1
              ? freshNotices[0].title
              : `Tienes ${freshNotices.length} avisos nuevos de reuniones.`,
          timeout: 6000,
          actions: [{ label: 'Ver', color: 'white', handler: () => openAlert(noticeAlert(freshNotices[0])) }],
        });
      knownNoticeIds = new Set(notices.map((notice) => notice.id));
      const reviews = result.filter((alert) => alert.kind === 'task_review');
      const fresh = reviews.filter((alert) => !knownReviewIds?.has(alert.id));
      if (fresh.length)
        q.notify({
          type: 'info',
          message:
            knownReviewIds === null
              ? reviews.length === 1
                ? 'Tienes una evidencia pendiente de revisión.'
                : `Tienes ${reviews.length} evidencias pendientes de revisión.`
              : 'Nueva evidencia pendiente de revisión.',
          timeout: 6000,
          actions: [{ label: 'Revisar', color: 'white', handler: () => openAlert(fresh[0]) }],
        });
      knownReviewIds = new Set(reviews.map((alert) => alert.id));
    } catch (e) {
      if (alertsOpen.value) q.notify({ type: 'negative', message: e.message });
    } finally {
      if (turn === alertSequence) loadingAlerts.value = false;
    }
  }
  watch(
    () => session.user?.id,
    (id) => {
      alerts.value = [];
      knownReviewIds = null;
      knownNoticeIds = null;
      alertSequence++;
      if (id) loadAlerts();
    },
    { immediate: true },
  );
  const refreshAlerts = () => {
    if (document.visibilityState !== 'hidden') loadAlerts();
  };
  onMounted(() => {
    alertTimer = setInterval(refreshAlerts, 30000);
    window.addEventListener('focus', refreshAlerts);
    window.addEventListener('ogc:task-review-changed', refreshAlerts);
    document.addEventListener('visibilitychange', refreshAlerts);
  });
  onUnmounted(() => {
    clearInterval(alertTimer);
    alertSequence++;
    window.removeEventListener('focus', refreshAlerts);
    window.removeEventListener('ogc:task-review-changed', refreshAlerts);
    document.removeEventListener('visibilitychange', refreshAlerts);
  });
  watch(
    () => route.path,
    () => {
      if (q.screen.lt.md) drawer.value = false;
    },
  );
  watch(
    () => session.user,
    (user) => {
      if (!user && route.path !== '/login') router.replace('/login');
    },
  );
  async function leave() {
    try {
      await logout();
      router.replace('/login');
    } catch (e) {
      q.notify({ type: 'negative', message: e.message });
    }
  }
  function find() {
    router.push({ path: '/tareas', query: { q: search.value } });
    search.value = '';
  }
</script>
<template>
  <router-view v-if="route.path === '/login'" />
  <q-layout v-else view="lHh Lpr lFf" class="app-layout">
    <q-header class="topbar"
      ><q-toolbar
        ><q-btn
          flat
          round
          icon="menu"
          aria-label="Abrir menú"
          class="mobile-menu"
          @click="drawer = !drawer"
        />
        <div class="breadcrumb">
          Espacio de trabajo <q-icon name="chevron_right" size="17px" /><b>{{
            route.meta.label
          }}</b>
        </div>
        <q-space /><q-input
          v-model="search"
          dense
          borderless
          placeholder="Buscar una tarea…"
          class="global-search"
          aria-label="Buscar una tarea"
          @keyup.enter="find"
          ><template #prepend><q-icon name="search" size="20px" /></template></q-input
        ><q-btn
          flat
          round
          icon="notifications_none"
          aria-label="Ver alertas"
          @click="
            alertsOpen = true;
            loadAlerts();
          "
          ><q-badge v-if="alerts.length" color="negative" floating rounded>{{
            alerts.length
          }}</q-badge></q-btn
        ><q-btn
          v-if="can('tasks.read')"
          flat
          round
          icon="cloud_sync"
          aria-label="Cuentas vinculadas"
          @click="router.push('/cuentas')"
          ><q-tooltip>Cuentas vinculadas</q-tooltip></q-btn
        ><span class="header-divider"></span
        ><q-avatar size="34px" class="user-avatar">{{ initials }}</q-avatar>
        <div class="header-user">
          <b>{{ session.user?.name }}</b
          ><small>{{ session.roles[0]?.replaceAll('_', ' ') }}</small>
        </div>
        <q-btn flat round icon="logout" aria-label="Cerrar sesión" @click="leave"
          ><q-tooltip>Cerrar sesión</q-tooltip></q-btn
        ></q-toolbar
      ></q-header
    >
    <q-drawer v-model="drawer" show-if-above :width="248" bordered class="sidebar"
      ><div class="sidebar-brand">
        <div class="brand-mark"><q-icon name="account_balance" size="25px" /></div>
        <div>
          <b>ROADMAP<span> OGC</span></b
          ><small>UNAJMA · Gestión de la Calidad</small>
        </div>
      </div>
      <div class="workspace-label"><span class="workspace-dot"></span> Espacio institucional</div>
      <div class="nav-caption">GESTIÓN Y SEGUIMIENTO</div>
      <q-list class="nav-list"
        ><q-item
          v-for="(m, index) in available"
          :key="m.path"
          clickable
          :to="m.path"
          :exact="m.path === '/'"
          active-class="nav-active"
          :class="{ 'nav-separator': index === 9 }"
          ><q-item-section avatar><q-icon :name="m.icon" size="21px" /></q-item-section
          ><q-item-section>{{ m.label }}</q-item-section
          ><q-item-section
            v-if="
              m.path === '/tareas' && alerts.filter((a) => a.entity === 'tasks' && a.overdue).length
            "
            side
            ><span class="nav-count">{{
              alerts.filter((a) => a.entity === 'tasks' && a.overdue).length
            }}</span></q-item-section
          ></q-item
        ></q-list
      >
      <div class="sidebar-bottom">
        <div class="quality-symbol"><q-icon name="eco" size="25px" /></div>
        <b>La calidad se construye<br />en equipo.</b
        ><small>Planificamos. Verificamos. Mejoramos.</small
        ><span class="version-label">ROADMAP OGC · UNAJMA</span>
      </div></q-drawer
    >
    <q-page-container
      ><div v-if="session.demo" class="demo-strip">
        <q-icon name="science" size="16px" />
        {{
          session.realParticipants
            ? 'Entorno local · Participantes del Excel y registros de demostración'
            : 'Entorno de prueba · Todos los registros son ficticios'
        }}
      </div>
      <router-view :key="route.path" />
      <footer class="app-footer">
        <span>Oficina de Gestión de la Calidad · UNAJMA</span
        ><span>Gestión conectada, mejora continua.</span>
      </footer></q-page-container
    >
    <q-dialog v-model="alertsOpen" position="right"
      ><q-card class="alerts-drawer"
        ><q-card-section class="row items-center"
          ><div>
            <span class="eyebrow">SEGUIMIENTO</span>
            <h3>Avisos y pendientes</h3>
            <p v-if="pendingReviewCount">
              {{ pendingReviewCount }}
              {{ pendingReviewCount === 1 ? 'evidencia pendiente' : 'evidencias pendientes' }} de
              revisión
            </p>
          </div>
          <q-space /><q-btn
            flat
            round
            icon="close"
            aria-label="Cerrar alertas"
            v-close-popup /></q-card-section
        ><q-linear-progress v-if="loadingAlerts" indeterminate /><q-list separator
          ><q-item
            v-for="alert in alerts"
            :key="`${alert.kind || alert.entity}:${alert.id}`"
            clickable
            @click="openAlert(alert)"
            ><q-item-section avatar
              ><q-icon
                :name="
                  alert.kind === 'task_review'
                    ? 'rate_review'
                    : alert.kind === 'notification'
                      ? 'groups'
                      : alert.overdue
                        ? 'schedule'
                        : 'event'
                "
                :color="alert.overdue ? 'negative' : 'primary'" /></q-item-section
            ><q-item-section
              ><q-item-label>{{ alert.title }}</q-item-label
              ><q-item-label caption>{{
                alert.kind === 'task_review'
                  ? `${alert.author} · Avance ${alert.progress}% · ${alert.label}`
                  : alert.kind === 'notification'
                    ? alert.message
                    : `${alert.label} · ${dateLabel(alert.due_date)}`
              }}</q-item-label></q-item-section
            ><q-item-section side
              ><span :class="alert.overdue ? 'text-negative' : 'text-primary'">{{
                alert.kind === 'task_review'
                  ? 'Por revisar'
                  : alert.kind === 'notification'
                    ? 'Nueva'
                    : alert.overdue
                      ? 'Vencido'
                      : 'Próximo'
              }}</span></q-item-section
            ></q-item
          ></q-list
        >
        <div v-if="!alerts.length && !loadingAlerts" class="empty-state">
          <q-icon name="notifications_paused" />
          <h3>Sin alertas por ahora</h3>
          <p>Los próximos plazos aparecerán aquí.</p>
        </div></q-card
      ></q-dialog
    >
  </q-layout>
</template>
