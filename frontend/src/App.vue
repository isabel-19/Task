<script setup>
  import { ref, computed, watch } from 'vue';
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
  const initials = computed(() =>
    session.user?.name
      .split(' ')
      .map((w) => w[0])
      .slice(0, 2)
      .join(''),
  );
  async function loadAlerts() {
    if (!session.user || !can('reports.read')) return;
    loadingAlerts.value = true;
    try {
      alerts.value = await api('/alerts');
    } catch (e) {
      q.notify({ type: 'negative', message: e.message });
    } finally {
      loadingAlerts.value = false;
    }
  }
  watch(
    () => session.user?.id,
    (id) => {
      if (id) loadAlerts();
    },
    { immediate: true },
  );
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
          @click="drawer = !drawer" />
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
        ><span class="header-divider"></span
        ><q-avatar size="34px" class="user-avatar">{{ initials }}</q-avatar>
        <div class="header-user">
          <b>{{ session.user?.name }}</b
          ><small>{{ session.roles[0]?.replaceAll('_', ' ') }}</small>
        </div>
        <q-btn flat round icon="logout" aria-label="Cerrar sesión" @click="leave" /></q-toolbar
    ></q-header>
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
        ><span class="version-label">ROADMAP OGC · v0.1</span>
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
            <h3>Alertas y próximos plazos</h3>
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
            :key="alert.id"
            clickable
            @click="
              router.push({
                path: entityRoutes[alert.entity],
                query: { resource: alert.entity, id: alert.id },
              });
              alertsOpen = false;
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
        <div v-if="!alerts.length && !loadingAlerts" class="empty-state">
          <q-icon name="notifications_paused" />
          <h3>Sin alertas por ahora</h3>
          <p>Los próximos plazos aparecerán aquí.</p>
        </div></q-card
      ></q-dialog
    >
  </q-layout>
</template>
