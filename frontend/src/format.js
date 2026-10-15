export const fieldLabels = {
  title: 'Nombre / asunto',
  name: 'Nombre',
  number: 'Número',
  description: 'Descripción',
  year: 'Año',
  date: 'Fecha',
  due_date: 'Plazo',
  start_date: 'Inicio',
  end_date: 'Fin',
  responsible_id: 'Responsable OGC',
  author_id: 'Autor',
  created_by: 'Asignada por',
  participants: 'Participantes',
  assigned_by: 'Asignada por',
  validated_by: 'Validado por',
  preparation_status: 'Estado de envío',
  sent_date: 'Fecha de envío',
  legacy_progress: 'Avance anterior sin validación individual',
  recurrence_source_id: 'Actividad de origen',
  theme: 'Temática / eje',
  progress: 'Avance',
  status: 'Estado',
  approval_status: 'Atención del documento recibido',
  document_status: 'Estado del documento',
  intake_format: 'Formato de recepción',
  notebook_number: 'N.º de registro del cuaderno',
  reference_text: 'Referencia del documento',
  followup_frequency: 'Frecuencia de seguimiento',
  receipt_number: 'Cargo o N.º de registro',
  comments: 'Comentarios / tareas pendientes',
  email_url: 'Enlace del correo',
  attended: 'Atendido',
  drafting_assistant_id: 'Asistente de redacción OGC',
  days_remaining: 'Días restantes',
  deadline_status: 'Situación del plazo',
  validation_status: 'Validación',
  review_status: 'Revisión del jefe',
  created_at: 'Fecha de registro',
  updated_at: 'Actualizado',
  action: 'Acción',
  actor_id: 'Usuario',
  entity: 'Entidad',
  record_id: 'Registro',
  comment: 'Comentario',
  note: 'Observación',
  justification: 'Justificación',
  kind: 'Tipo de aporte',
  case_id: 'Expediente',
  approver_id: 'Aprobador',
  validator_id: 'Validador',
  reviewer_id: 'Revisor',
  evidence_version_id: 'Versión de evidencia',
  task_update_id: 'Aporte',
  deliverable_id: 'Entregable',
  filename: 'Archivo',
  sha256: 'Huella del archivo',
  backup_path: 'Archivo de respaldo',
  batch_id: 'Lote de importación',
  sheet: 'Hoja',
  row_number: 'Fila de origen',
  before: 'Valores anteriores',
  after: 'Valores posteriores',
  preview: 'Previsualización',
  mapping: 'Mapeo de columnas',
  version: 'Versión',
  email: 'Correo',
  password: 'Contraseña',
  member_ids: 'Participantes',
  user_id: 'Integrante',
  role_id: 'Rol',
  permission_id: 'Permiso',
  task_id: 'Tarea',
  project_id: 'Proyecto',
  document_id: 'Documento',
  evidence_id: 'Evidencia',
  meeting_id: 'Reunión',
  agreement_id: 'Acuerdo',
  indicator_id: 'Indicador',
  period_id: 'Periodo',
  axis_id: 'Eje temático',
  process_id: 'Proceso',
  document_type_id: 'Tipo documental',
  service_order_id: 'Orden de servicio',
  criterion_id: 'Criterio',
  quality_model_id: 'Modelo de calidad',
  url: 'Enlace autorizado',
  access_confirmed: 'Permisos de acceso',
  resolution_id: 'Resolución',
  evidence_title: 'Nombre de la evidencia',
  evidence_url: 'Enlace de la evidencia',
  evidence_access: 'Acceso a la evidencia',
  target: 'Meta',
  result: 'Resultado',
};
const states = {
  por_inicio: 'Por inicio',
  en_redaccion: 'En redacción',
  listo_para_envio: 'Listo para envío',
  enviado_digital: 'Enviado digital',
  enviado_fisico: 'Enviado físico',
  enviado_fisico_y_digital: 'Enviado físico y digital',
  enviado: 'Enviado',
  enviado_sin_medio: 'Enviado (medio sin registrar)',
  elaborado: 'Elaborado (registro anterior)',
  remitido: 'Enviado (medio sin registrar)',
  compartido: 'Compartido con las áreas participantes',
  en_reunion: 'En reunión',
  para_revision: 'Para revisión',
  pendiente_atencion: 'Pendiente de atención',
  fisico: 'Físico',
  ambos: 'Ambos (físico y digital)',
  no_es_necesario: 'No es necesario',
  sin_plazo: 'Determinar fecha límite',
  completo: 'Completo',
  en_plazo: 'Dentro del plazo',
  pendiente_validacion: 'Pendiente de validación',
  pendiente_revision: 'Pendiente de revisión',
  envio_anterior: 'Envío anterior',
  en_progreso: 'En progreso',
  en_revision: 'En revisión',
  en_pausa: 'En pausa',
  elaboracion: 'Elaboración',
  revision: 'Revisión',
  derivacion: 'Derivación',
  subsanacion: 'Subsanación',
  comentario: 'Comentario',
  observacion: 'Observación',
  consulta_auditoria: 'Consulta / auditoría',
  preview: 'Previsualización',
  committed: 'Importado',
};
export function human(value) {
  const text = String(value ?? '');
  return states[text] || text.replaceAll('_', ' ').replace(/^\w/, (c) => c.toUpperCase());
}
export function fieldLabel(key, fallback) {
  return fieldLabels[key] || fallback || human(key);
}
export function formatApiError(detail) {
  if (Array.isArray(detail))
    return detail
      .map((error) => {
        const keys = (error.loc || []).filter((key) => !['body', 'query', 'path'].includes(key));
        const key = keys.at(-1);
        const label =
          error.label ||
          (keys.includes('evidence')
            ? {
                title: 'Nombre de la evidencia',
                url: 'Enlace de la evidencia',
                access_confirmed: 'Acceso a la evidencia',
              }[key]
            : null) ||
          fieldLabel(key || 'Campo');
        const legacy = {
          missing: 'Este campo es obligatorio.',
          extra_forbidden: 'Este campo no está permitido.',
          int_parsing: 'Ingresa un número entero.',
          float_parsing: 'Ingresa un número válido.',
          string_too_short: 'Completa este campo con un valor válido.',
        };
        const message = error.label
          ? error.msg
          : legacy[error.type] ||
            (error.msg === 'Field required' ? 'Este campo es obligatorio.' : error.msg);
        return `${label}: ${message || 'Revisa el valor de este campo.'}`;
      })
      .join('\n');
  return typeof detail === 'string'
    ? detail
    : 'No se pudo completar la solicitud. Revisa los datos e inténtalo de nuevo.';
}
export function calendarDay(value) {
  return Date.parse(`${String(value).slice(0, 10)}T00:00:00Z`);
}
