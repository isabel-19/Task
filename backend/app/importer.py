"""CSV/XLSX preview and transactional import, preserving byte-identical originals."""
import base64
import csv
import hashlib
import io
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, UniqueConstraint
from . import models as m
from .db import get_db
from .security import current_user, require
from .config import settings
from .catalog import RESOURCES
from .service import resource, validate_data, check_business, audit, serialize

router = APIRouter()
ALLOWED = {'projects', 'tasks', 'documents', 'meetings', 'agreements', 'service-orders', 'deliverables', 'indicators', 'indicator-results'}
NAMESPACE = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main', 'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
STORAGE = Path(__file__).resolve().parents[1] / 'storage/imports'


def normalize(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value)).strip().lower().split())


def read_xml(archive, name):
    data = archive.read(name)
    if b'<!DOCTYPE' in data:
        raise HTTPException(422, 'No se admiten XML con DTD.')
    return ET.fromstring(data)


def read_source(filename, data, selected_sheet=None):
    suffix = Path(filename).suffix.lower()
    links = []
    if suffix == '.csv':
        try:
            text = data.decode('utf-8-sig')
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=',;\t')
            rows = list(csv.reader(io.StringIO(text), dialect))
        except (UnicodeDecodeError, csv.Error):
            raise HTTPException(422, 'CSV no válido. Guarda el archivo en UTF-8 con encabezados.')
        sheet, sheets = 'CSV', ['CSV']
    elif suffix == '.xlsx':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(i.file_size for i in archive.infolist()) > 20_000_000 or len(archive.infolist()) > 2000:
                    raise HTTPException(422, 'El libro excede el límite descomprimido de 20 MB.')
                workbook = read_xml(archive, 'xl/workbook.xml')
                if workbook.find('s:workbookPr', NAMESPACE) is not None and workbook.find('s:workbookPr', NAMESPACE).get('date1904') == '1':
                    raise HTTPException(422, 'Convierte las fechas del libro 1904 a texto ISO antes de importar.')
                rels = {r.get('Id'): r.get('Target') for r in read_xml(archive, 'xl/_rels/workbook.xml.rels')}
                available = list(workbook.find('s:sheets', NAMESPACE))
                sheets = [s.get('name') for s in available]
                sheet = selected_sheet or sheets[0]
                chosen = next((s for s in available if s.get('name') == sheet), None)
                if chosen is None:
                    raise HTTPException(422, 'Hoja no encontrada en el libro.')
                target = rels[chosen.get('{' + NAMESPACE['r'] + '}id')]
                path = target.lstrip('/') if target.startswith('/') else 'xl/' + target
                shared = []
                if 'xl/sharedStrings.xml' in archive.namelist():
                    for item in read_xml(archive, 'xl/sharedStrings.xml'):
                        shared.append(''.join(t.text or '' for t in item.iter('{' + NAMESPACE['s'] + '}t')))
                rows = []
                for row in read_xml(archive, path).findall('s:sheetData/s:row', NAMESPACE):
                    values = []
                    for cell in row:
                        letters = ''.join(c for c in cell.get('r', '') if c.isalpha())
                        index = 0
                        for letter in letters:
                            index = index * 26 + ord(letter.upper()) - 64
                        if index > 200:
                            raise HTTPException(422, 'Máximo 200 columnas por hoja.')
                        while len(values) < index:
                            values.append('')
                        value = cell.find('s:v', NAMESPACE)
                        text = value.text if value is not None else ''
                        if cell.get('t') == 's':
                            text = shared[int(text)] if text else ''
                        elif cell.get('t') == 'inlineStr':
                            text = ''.join(t.text or '' for t in cell.iter('{' + NAMESPACE['s'] + '}t'))
                        if index:
                            values[index - 1] = text
                    rows.append(values)
                for name in archive.namelist():
                    if name.endswith('.rels'):
                        for rel in read_xml(archive, name):
                            if rel.get('TargetMode') == 'External':
                                links.append({'source': name, 'url': rel.get('Target'), 'reviewed': False})
        except (zipfile.BadZipFile, KeyError, IndexError, ValueError, ET.ParseError):
            raise HTTPException(422, 'Libro XLSX no válido o no compatible.')
    else:
        raise HTTPException(422, 'Se admiten CSV UTF-8 y XLSX. Convierte XLS a XLSX sin alterar el original.')
    if not rows or not rows[0] or len(rows) > 1001:
        raise HTTPException(422, 'La fuente debe tener encabezados y un máximo de 1 000 filas por hoja.')
    headers = [normalize(h) for h in rows[0]]
    if len(set(headers)) != len(headers) or any(not h for h in headers):
        raise HTTPException(422, 'Los encabezados deben ser únicos y no estar vacíos después de normalizarlos.')
    records = [(i, dict(zip(headers, row))) for i, row in enumerate(rows[1:], start=2) if any(str(v).strip() for v in row)]
    return headers, records, sheet, sheets, links


class PreviewInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    filename: str = Field(min_length=1, max_length=250)
    content_base64: str = Field(max_length=7_000_000)
    entity: str
    sheet: str | None = None
    # Field -> original column heading. Constants (e.g. responsible/project UUID) are separate.
    mapping: dict[str, str] = Field(default_factory=dict)
    constants: dict = Field(default_factory=dict)


def check_duplicates(db, model, data, seen):
    unique_keys = [[c.name for c in constraint.columns] for constraint in model.__table__.constraints if isinstance(constraint, UniqueConstraint)]
    unique_keys += [[c.key] for c in model.__table__.columns if c.unique]
    if not unique_keys:
        logical = [key for key in ('title', 'project_id', 'responsible_id', 'due_date', 'date') if key in data]
        unique_keys = [logical] if logical else []
    for keys in unique_keys:
        if any(data.get(key) is None for key in keys):
            continue
        key = tuple((k, str(data[k])) for k in keys)
        if key in seen:
            raise HTTPException(409, 'Duplicado dentro de la fuente.')
        if db.scalar(select(model.id).where(*[getattr(model, k) == data[k] for k in keys])):
            raise HTTPException(409, 'Registro ya existente en la base de datos.')
        seen.add(key)


def validate_row(db, entity, model, data, seen):
    clean = validate_data(entity, data)
    check_business(db, entity, clean)
    for column in model.__table__.columns:
        if column.foreign_keys and clean.get(column.key):
            target = next(iter(column.foreign_keys)).column.table.name
            target_model = next((spec[0] for spec in RESOURCES.values() if spec[0].__tablename__ == target), None)
            if target_model and not db.get(target_model, clean[column.key]):
                raise HTTPException(422, f'Referencia inexistente: {column.key}. Usa el UUID de un registro previo.')
    check_duplicates(db, model, clean, seen)
    return clean


@router.post('/preview')
def preview(body: PreviewInput, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'admin.write')
    if not settings.imports_enabled:
        raise HTTPException(403, 'La importación está deshabilitada hasta configurar un respaldo persistente en este entorno.')
    if body.entity not in ALLOWED:
        raise HTTPException(422, 'Entidad no habilitada para importación.')
    try:
        data = base64.b64decode(body.content_base64, validate=True)
    except ValueError:
        raise HTTPException(422, 'Contenido de archivo no válido.')
    if len(data) > 5_000_000:
        raise HTTPException(422, 'Máximo 5 MB por archivo.')
    headers, rows, sheet, sheets, links = read_source(body.filename, data, body.sheet)
    if not body.mapping:
        return {'headers': headers, 'sheets': sheets, 'sheet': sheet, 'external_links': links, 'sample': rows[:5], 'row_count': len(rows)}
    model, _, _ = resource(body.entity)
    errors, clean_rows, seen = [], [], set()
    for number, row in rows:
        try:
            mapped = {key: row.get(normalize(header), '') for key, header in body.mapping.items()}
            mapped = {k: v for k, v in mapped.items() if v != ''}
            clean = validate_row(db, body.entity, model, mapped | body.constants, seen)
            clean_rows.append({'row': number, 'data': jsonable_encoder(clean)})
        except HTTPException as error:
            errors.append({'row': number, 'error': error.detail})
    sha = hashlib.sha256(data).hexdigest()
    STORAGE.mkdir(parents=True, exist_ok=True)
    backup = STORAGE / (sha + Path(body.filename).suffix.lower())
    if not backup.exists():
        backup.write_bytes(data)
    if hashlib.sha256(backup.read_bytes()).hexdigest() != sha:
        raise HTTPException(409, 'La copia de respaldo no coincide con la fuente.')
    result = {'rows': clean_rows, 'errors': errors, 'external_links': links, 'headers': headers, 'sheet': sheet}
    batch = m.ImportBatch(filename=Path(body.filename).name, sha256=sha, sheet=sheet, entity=body.entity,
                          backup_path=backup.name, mapping={'columns': body.mapping, 'constants': body.constants},
                          preview=result, modified_by=user.id)
    db.add(batch)
    audit(db, user, 'import-batches', batch, 'preview')
    db.commit()
    return {'id': batch.id, 'sha256': sha, 'valid_count': len(clean_rows), 'error_count': len(errors), **result}


@router.post('/commit/{identifier}')
def commit(identifier: str, user=Depends(current_user), db=Depends(get_db)):
    require(db, user, 'admin.write')
    if not settings.imports_enabled:
        raise HTTPException(403, 'La importación está deshabilitada en este entorno.')
    batch = db.scalar(select(m.ImportBatch).where(m.ImportBatch.id == identifier).with_for_update())
    if not batch:
        raise HTTPException(404, 'Previsualización no encontrada.')
    if batch.status != 'preview' or batch.preview['errors']:
        raise HTTPException(409, 'La importación debe ser nueva y no tener errores.')
    original = STORAGE / batch.backup_path
    if not original.exists() or hashlib.sha256(original.read_bytes()).hexdigest() != batch.sha256:
        raise HTTPException(409, 'Verificación del respaldo fallida.')
    model, _, _ = resource(batch.entity)
    seen = set()
    before = serialize(batch)
    for row in batch.preview['rows']:
        clean = validate_row(db, batch.entity, model, row['data'], seen)
        if batch.entity == 'tasks':
            clean['created_by'] = user.id
        item = model(**clean, modified_by=user.id)
        db.add(item)
        audit(db, user, batch.entity, item, 'import')
        db.add(m.ImportSource(batch_id=batch.id, sheet=batch.sheet, row_number=row['row'], entity=batch.entity, record_id=item.id, modified_by=user.id))
    batch.status, batch.modified_by, batch.revision = 'imported', user.id, batch.revision + 1
    audit(db, user, 'import-batches', batch, 'commit', before)
    db.commit()
    return {'imported': len(batch.preview['rows']), 'batch_id': batch.id}
