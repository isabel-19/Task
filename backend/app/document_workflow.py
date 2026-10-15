"""Issuance states from the reference register, distinct from received-document attention."""
from fastapi import HTTPException
from . import models as m

SEND_STATES = ['enviado_digital', 'enviado_fisico', 'enviado_fisico_y_digital']
BASE_STATES = ['por_inicio', 'en_redaccion', *SEND_STATES]
DOCUMENT_STATES = [*BASE_STATES, 'listo_para_envio', 'anulado', 'para_revision',
                   'programada', 'en_reunion', 'compartido', 'enviado']


def status_options(type_name):
    # Import locally to avoid the registry/service import cycle.
    from .document_registry import series_key
    key = series_key(type_name)
    if key == 'acta':
        return ['programada', 'en_reunion', 'en_redaccion', 'compartido', 'enviado']
    if key == 'informe-tecnico':
        return BASE_STATES
    if key == 'carta-multiple':
        return [*BASE_STATES, 'anulado']
    if key == 'informe':
        return [*BASE_STATES, 'listo_para_envio', 'para_revision']
    return [*BASE_STATES, 'listo_para_envio', 'anulado']


def is_sent(status):
    return status in [*SEND_STATES, 'compartido', 'enviado', 'remitido']


def validate_workflow(db, data, existing=None):
    if data.get('priority') not in [None, 'baja', 'media', 'alta']:
        raise HTTPException(422, 'Selecciona prioridad alta, media o baja, como en el registro documental.')
    section = data.get('section', existing.section if existing else None)
    if section != 'emitidos':
        return
    state = data.get('preparation_status', existing.preparation_status if existing else 'por_inicio')
    typ = db.get(m.DocumentType, data.get('document_type_id', existing.document_type_id if existing else None))
    options = status_options(typ.name) if typ else DOCUMENT_STATES
    # Preserve previously registered sends whose medium was not captured.
    legacy = existing and state == existing.preparation_status and state in ['elaborado', 'remitido', 'enviado']
    if state not in options and not legacy:
        raise HTTPException(422, 'Selecciona un estado del registro correspondiente al tipo documental.')
    sent_date = data.get('sent_date', existing.sent_date if existing else None)
    if is_sent(state) and not sent_date:
        raise HTTPException(422, 'Registra la fecha del envío o de la distribución del acta.')
    if not is_sent(state) and sent_date:
        raise HTTPException(422, 'Un documento sin enviar no puede tener fecha de envío.')


def display_status(document):
    if document.section == 'recibidos':
        return 'atendido' if document.attended else ('pendiente_atencion' if document.approval_status == 'pendiente' else document.approval_status)
    if document.section == 'emitidos':
        return {'elaborado': 'listo_para_envio', 'remitido': 'enviado_sin_medio'}.get(document.preparation_status, document.preparation_status)
    return 'archivado' if document.section == 'archivo' else 'registrado'
