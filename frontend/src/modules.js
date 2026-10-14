export const modules = [
  {
    path: '/',
    label: 'Dashboard',
    icon: 'space_dashboard',
    permission: 'reports.read',
    subtitle: 'Tu panorama de la gestión de calidad',
    resources: [],
  },
  {
    path: '/proyectos',
    label: 'Proyectos y Roadmap',
    icon: 'route',
    permission: 'projects.read',
    subtitle: 'Del plan institucional a cada hito',
    resources: ['projects', 'milestones', 'axes', 'processes', 'task-dependencies'],
  },
  {
    path: '/tareas',
    label: 'Tareas y responsables',
    icon: 'task_alt',
    permission: 'tasks.read',
    subtitle: 'Organiza, avanza y cierra con evidencia',
    resources: ['tasks', 'task-assignments', 'task-updates', 'closure-approvals'],
  },
  {
    path: '/registro',
    label: 'Registro Digital',
    icon: 'folder_open',
    permission: 'documents.read',
    subtitle: 'Un registro único para cada documento',
    resources: ['documents', 'document-versions', 'task-documents', 'document-types'],
  },
  {
    path: '/tramites',
    label: 'Seguimiento de trámites',
    icon: 'account_tree',
    permission: 'cases.read',
    subtitle: 'Cada actuación, hasta la aprobación',
    resources: ['cases', 'case-events'],
  },
  {
    path: '/reuniones',
    label: 'Reuniones y acuerdos',
    icon: 'groups',
    permission: 'meetings.read',
    subtitle: 'Convierte los acuerdos en acciones',
    resources: ['meetings', 'agreements', 'attendees'],
  },
  {
    path: '/evidencias',
    label: 'Evidencias',
    icon: 'verified',
    permission: 'evidence.read',
    subtitle: 'Medios de verificación y solicitudes a otras áreas',
    resources: ['evidence', 'evidence-versions', 'evidence-links', 'evidence-validations'],
  },
  {
    path: '/servicios',
    label: 'Entregables OS',
    icon: 'inventory_2',
    permission: 'services.read',
    subtitle: 'Plazos, observaciones y conformidad de servicios',
    resources: ['deliverables', 'service-orders', 'deliverable-reviews'],
  },
  {
    path: '/indicadores',
    label: 'Indicadores y calidad',
    icon: 'insights',
    permission: 'indicators.read',
    subtitle: 'Metas, resultados y planes de mejora',
    resources: [
      'indicators',
      'indicator-results',
      'quality-models',
      'criteria',
      'periods',
      'improvement-plans',
    ],
  },
  {
    path: '/reportes',
    label: 'Reportes y alertas',
    icon: 'summarize',
    permission: 'reports.read',
    subtitle: 'Información para decidir y actuar',
    resources: [],
  },
  {
    path: '/administracion',
    label: 'Administración',
    icon: 'settings',
    permission: ['admin.read', 'audit.read'],
    subtitle: 'Usuarios, permisos, catálogos y trazabilidad',
    resources: [
      'users',
      'user-roles',
      'roles',
      'role-permissions',
      'permissions',
      'audit',
      'import-batches',
      'import-sources',
    ],
  },
];
export const entityRoutes = Object.fromEntries(
  modules.flatMap((m) => m.resources.map((r) => [r, m.path])),
);
entityRoutes['tasks'] = '/tareas';
export const titles = { pending: 'Pendientes', overdue: 'Vencidas' };
export function human(value) {
  return String(value ?? '')
    .replaceAll('_', ' ')
    .replace(/^\w/, (c) => c.toUpperCase());
}
export function dateLabel(value) {
  if (!value) return '—';
  const d = new Date(value.includes('T') ? value : value + 'T12:00:00');
  return isNaN(d)
    ? value
    : new Intl.DateTimeFormat('es-PE', { day: '2-digit', month: 'short', year: 'numeric' }).format(
        d,
      );
}
