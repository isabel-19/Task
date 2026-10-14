import { createRouter, createWebHistory } from 'vue-router';
import { modules } from './modules';
import { session, restoreSession, can } from './api';
import LoginView from './views/LoginView.vue';
import DashboardView from './views/DashboardView.vue';
import ModuleView from './views/ModuleView.vue';
import ReportsView from './views/ReportsView.vue';

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    ...modules.map((m) => ({
      path: m.path,
      component: m.path === '/' ? DashboardView : m.path === '/reportes' ? ReportsView : ModuleView,
      meta: m,
    })),
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
});
router.beforeEach(async (to) => {
  if (!session.ready) {
    try {
      await restoreSession();
    } catch {
      return to.path === '/login' ? true : '/login';
    }
  }
  if (to.path !== '/login' && !session.user)
    return { path: '/login', query: { next: to.fullPath } };
  if (to.path === '/login' && session.user) return '/';
  if (to.meta.permission && !can(to.meta.permission)) return '/';
});
