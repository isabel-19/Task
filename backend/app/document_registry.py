"""Document links and independent annual OGC numbering, based on the reference register."""
import re
import unicodedata
from sqlalchemy import select, case
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from fastapi import HTTPException
from . import models as m
from .service import get_record, document_url, audit

SERIES = {
    'carta': ('Carta', 'CARTA', 'UNAJMA-OGC'),
    'carta-multiple': ('Carta múltiple', 'CARTA MÚLTIPLE', 'UNAJMA-OGC'),
    'informe': ('Informe', 'INFORME', 'UNAJMA-OGC'),
    'informe-tecnico': ('Informe técnico', 'INFORME TÉCNICO', 'UNAJMA/OGC'),
    'oficio': ('Oficio', 'OFICIO', 'UNAJMA-OGC'),
    'acta': ('Acta de reunión', 'ACTA DE REUNIÓN', 'UNAJMA-OGC-SGCI'),
}


def series_key(name):
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if not unicodedata.combining(c))
    name = re.sub(r'\s*\([^)]*\)\s*', ' ', name).strip().lower()
    name = re.sub(r'\s+', ' ', name)
    return {
        'carta': 'carta', 'carta simple': 'carta', 'cartas simples': 'carta',
        'carta multiple': 'carta-multiple', 'cartas multiples': 'carta-multiple',
        'informe': 'informe', 'informes': 'informe',
        'informe tecnico': 'informe-tecnico', 'informes tecnicos': 'informe-tecnico',
        'oficio': 'oficio', 'oficios': 'oficio',
        'acta': 'acta', 'acta de reunion': 'acta', 'actas': 'acta',
    }.get(name)


def format_number(series, year, number):
    _, prefix, suffix = SERIES[series]
    return f'{prefix} N° {number:03d}-{year}-{suffix}'


def document_choices(db):
    batch = db.scalar(select(m.ImportBatch).where(m.ImportBatch.entity == 'document-catalogs', m.ImportBatch.status == 'imported')
                      .order_by(m.ImportBatch.created_at.desc(), m.ImportBatch.id).limit(1))
    names = batch.preview.get('recipients', []) if batch else []
    from .document_workflow import status_options
    return {'document-recipients': [{'value': name, 'label': name} for name in names],
            'document-statuses': {typ.id: status_options(typ.name) for typ in db.scalars(select(m.DocumentType))}}


def document_fields(db, raw, existing=None):
    raw = dict(raw)
    section = raw.get('section', existing.section if existing else None)
    if section == 'emitidos' and not existing and 'preparation_status' not in raw:
        from .document_workflow import status_options
        typ = get_record(db, m.DocumentType, raw.get('document_type_id'))
        raw['preparation_status'] = status_options(typ.name)[0]
    if section == 'emitidos' and not raw.get('sender'):
        identifier = raw.get('responsible_id', existing.responsible_id if existing else None)
        if identifier and (not existing or identifier != existing.responsible_id):
            if not isinstance(identifier, str):
                raise HTTPException(422, 'Selecciona un remitente válido del equipo OGC.')
            raw['sender'] = get_record(db, m.User, identifier).name
    choices = {option['value'] for option in document_choices(db)['document-recipients']}
    for key in ['recipient', *(['sender'] if section == 'recibidos' else [])]:
        if key in raw and choices and (not existing or raw[key] != getattr(existing, key)) and (not isinstance(raw[key], str) or raw[key] not in choices):
            raise HTTPException(422, 'Selecciona la oficina o entidad del desplegable del registro documental.')
    return raw


def last_registered(db, series, year):
    # Alias types share a series; foreign received numbers never affect OGC issuance.
    records = db.execute(select(m.Document.number, m.DocumentType.name)
                         .join(m.DocumentType, m.Document.document_type_id == m.DocumentType.id)
                         .where(m.Document.year == year, m.Document.section == 'emitidos'))
    floor = 0
    for number, type_name in records:
        if series_key(type_name) != series:
            continue
        match = re.search(r'N[°ºª.]?\s*(\d+)\s*[-–—]\s*(\d{4})', number, re.I)
        if match and int(match[2]) == year:
            floor = max(floor, int(match[1]))
    return floor


def next_number(db, type_id, year, section='emitidos', reserve=False):
    typ = get_record(db, m.DocumentType, type_id)
    key = series_key(typ.name)
    if section != 'emitidos' or not key:
        return {'automatic': False, 'number': None, 'message': 'Conserva el número o código original del documento.'}
    floor = last_registered(db, key, year)
    if reserve:
        insert = postgres_insert if db.get_bind().dialect.name == 'postgresql' else sqlite_insert
        table = m.DocumentSequence.__table__
        statement = insert(table).values(series=key, year=year, last_number=floor + 1)
        statement = statement.on_conflict_do_update(
            index_elements=[table.c.series, table.c.year],
            set_={'last_number': case((table.c.last_number >= floor, table.c.last_number + 1), else_=floor + 1)},
        ).returning(table.c.last_number)
        number = db.scalar(statement)
    else:
        current = db.get(m.DocumentSequence, (key, year))
        number = max(floor, current.last_number if current else 0) + 1
    return {'automatic': True, 'number': format_number(key, year, number), 'sequence': number, 'series': key, 'year': year}


def document_input(body, existing=None):
    raw = dict(body)
    explicit_numbering = 'automatic_number' in raw
    automatic = raw.pop('automatic_number', False)
    if not isinstance(automatic, bool):
        raise HTTPException(422, 'La opción de numeración automática debe ser válida.')
    if existing and automatic:
        raise HTTPException(422, 'La edición conserva el número asignado. Desactiva la numeración automática.')
    if not existing and not explicit_numbering and not str(raw.get('number') or '').strip() and raw.get('section') == 'emitidos':
        automatic = True
    if automatic:
        if raw.get('section') != 'emitidos':
            raise HTTPException(422, 'La numeración OGC automática corresponde a documentos emitidos.')
        raw['number'] = 'PENDIENTE DE ASIGNACIÓN'
    url = raw.pop('url', None)
    confirmed = raw.pop('access_confirmed', False)
    if not isinstance(confirmed, bool):
        raise HTTPException(422, 'Confirma los permisos del enlace con una opción válida.')
    if url is not None and not isinstance(url, str):
        raise HTTPException(422, 'Pega el enlace del documento como texto.')
    url = document_url(url.strip()) if url and url.strip() else None
    return raw, automatic, (url, confirmed)


def save_link(db, user, document, link):
    url, confirmed = link
    if not url:
        return
    # Serialize version creation with edits to the parent document.
    current = db.scalar(select(m.DocumentVersion).where(m.DocumentVersion.document_id == document.id)
                        .order_by(m.DocumentVersion.version.desc()).limit(1))
    if current and current.url == url and current.access_confirmed == confirmed:
        return
    version = m.DocumentVersion(document_id=document.id, version=(current.version if current else 0) + 1,
                                url=url, access_confirmed=confirmed, author_id=user.id, modified_by=user.id)
    db.add(version)
    audit(db, user, 'document-versions', version, 'create')
