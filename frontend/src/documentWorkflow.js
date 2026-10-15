export const sendStates = ['enviado_digital', 'enviado_fisico', 'enviado_fisico_y_digital'];
export function isSent(status) {
  return [...sendStates, 'compartido', 'enviado', 'remitido'].includes(status);
}
export function documentState(row) {
  row ||= {};
  if (row.document_status) return row.document_status;
  if (row.section === 'recibidos') return row.attended ? 'atendido' :
    (row.approval_status && row.approval_status !== 'pendiente' ? row.approval_status : 'pendiente_atencion');
  if (row.section === 'archivo') return 'archivado';
  if (row.section === 'normativos') return 'registrado';
  return ({ elaborado: 'listo_para_envio', remitido: 'enviado_sin_medio' })[row.preparation_status] || row.preparation_status || 'por_inicio';
}
export function statusOptions(lookups, type, fallback = []) {
  return lookups?.['document-statuses']?.[type] || fallback;
}
