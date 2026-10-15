"""Bounded private evidence storage and content-only document previews."""
import csv
import hashlib
import io
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException
from .config import settings
from .evidence_objects import stored_path, put_object, discard_object

TYPES = {
    '.pdf': 'application/pdf', '.png': 'image/png', '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.txt': 'text/plain', '.csv': 'text/csv',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}
SIZE_MESSAGE = 'El archivo supera el tamaño máximo permitido.'


def upload_limit():
    return max(1, min(settings.evidence_max_upload_mb, 50)) * 1024 * 1024


def storage_root():
    return Path(settings.evidence_storage_dir).resolve() if settings.evidence_storage_dir else Path(__file__).resolve().parents[1] / 'storage/evidence'


def clean_name(name):
    name = unicodedata.normalize('NFC', (name or '').replace('\\', '/').split('/')[-1])
    name = ''.join(c for c in name if unicodedata.category(c)[0] != 'C').strip(' .')
    if not name or len(name) > 250:
        raise HTTPException(422, 'Usa un nombre de archivo de hasta 250 caracteres.')
    return name


def text_content(data):
    try:
        text = data.decode('utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
    except UnicodeError:
        raise HTTPException(422, 'El archivo de texto debe usar UTF-8 o UTF-16.')
    if any(ord(c) < 32 and c not in '\r\n\t' for c in text):
        raise HTTPException(422, 'El archivo no contiene texto válido.')
    return text


def safe_xml(archive, name):
    if archive.getinfo(name).file_size > 4 * 1024 * 1024:
        raise HTTPException(422, 'El documento contiene una sección demasiado grande para procesarla.')
    data = archive.read(name)
    markup = data.replace(b'\x00', b'').upper()
    if b'<!DOCTYPE' in markup or b'<!ENTITY' in markup:
        raise HTTPException(422, 'El documento contiene XML no admitido.')
    return ET.fromstring(data)


def office_archive(data, suffix):
    archive = zipfile.ZipFile(io.BytesIO(data))
    entries = archive.infolist()
    required = 'word/document.xml' if suffix == '.docx' else 'xl/workbook.xml'
    if len(entries) > 2000 or sum(e.file_size for e in entries) > 50 * 1024 * 1024:
        archive.close()
        raise HTTPException(422, 'El documento comprimido supera los límites de procesamiento.')
    names = archive.namelist()
    if required not in names or '[Content_Types].xml' not in names or any('vbaproject' in n.lower() for n in names):
        archive.close()
        raise HTTPException(422, 'Usa un documento DOCX o XLSX válido, sin macros.')
    return archive


def validate_content(data, suffix):
    valid = {
        '.pdf': lambda: data.startswith(b'%PDF-') and b'%%EOF' in data[-2048:],
        '.png': lambda: data.startswith(b'\x89PNG\r\n\x1a\n'),
        '.jpg': lambda: data.startswith(b'\xff\xd8\xff'),
        '.jpeg': lambda: data.startswith(b'\xff\xd8\xff'),
        '.webp': lambda: data.startswith(b'RIFF') and data[8:12] == b'WEBP',
    }
    if suffix in valid and not valid[suffix]():
        raise HTTPException(422, 'El contenido del archivo no corresponde a su extensión.')
    if suffix in {'.txt', '.csv'}:
        text_content(data)
    if suffix in {'.docx', '.xlsx'}:
        try:
            with office_archive(data, suffix) as archive:
                safe_xml(archive, 'word/document.xml' if suffix == '.docx' else 'xl/workbook.xml')
        except (zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, ValueError):
            raise HTTPException(422, 'El documento está dañado o protegido con contraseña.')


async def store_upload(upload):
    name = clean_name(upload.filename)
    suffix = Path(name).suffix.lower()
    if suffix not in TYPES:
        raise HTTPException(422, 'Formato no admitido. Usa PDF, PNG, JPG, WEBP, DOCX, XLSX, TXT o CSV.')
    data = await upload.read(upload_limit() + 1)
    if len(data) > upload_limit():
        raise HTTPException(413, SIZE_MESSAGE)
    if not data:
        raise HTTPException(422, 'Selecciona un archivo que tenga contenido.')
    validate_content(data, suffix)
    key = uuid4().hex
    try:
        await put_object(key, data, TYPES[suffix])
    except Exception:
        # Also handles an uncertain provider response after an upload.
        await discard_object(key)
        raise
    return {'storage_key': key, 'file_name': name, 'content_type': TYPES[suffix],
            'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def file_metadata(record):
    return {'id': record.id, 'name': record.file_name, 'content_type': record.content_type,
            'size': record.byte_size, 'url': '/api/evidence-files/' + record.id,
            'source': {'provider': record.source_provider, 'url': record.source_url} if record.source_provider else None}


def document_preview(path, name):
    return document_preview_bytes(path.read_bytes(), name)


def document_preview_bytes(data, name):
    """Extract values as data, never HTML, scripts, Office macros or external links."""
    suffix = Path(name).suffix.lower()
    limit = 100000
    try:
        if suffix == '.txt':
            text = text_content(data)
            return {'kind': 'text', 'text': text[:limit], 'truncated': len(text) > limit}
        if suffix == '.csv':
            text = text_content(data)
            try:
                dialect = csv.Sniffer().sniff(text[:8192], delimiters=',;\t|')
            except csv.Error:
                dialect = csv.excel
            rows = []
            truncated = False
            for index, row in enumerate(csv.reader(io.StringIO(text), dialect)):
                if index >= 100:
                    truncated = True
                    break
                truncated |= len(row) > 20 or any(len(cell) > 2000 for cell in row)
                rows.append([cell[:2000] for cell in row[:20]])
            return {'kind': 'table', 'sheets': [{'name': name, 'rows': rows}], 'truncated': truncated}
        with office_archive(data, suffix) as archive:
            if suffix == '.docx':
                root = safe_xml(archive, 'word/document.xml')
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text = '\n'.join(''.join(p.itertext()) for p in root.findall('.//w:p', ns))
                return {'kind': 'text', 'text': text[:limit], 'truncated': len(text) > limit}
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            strings = []
            if 'xl/sharedStrings.xml' in archive.namelist():
                strings = [''.join(el.itertext()) for el in safe_xml(archive, 'xl/sharedStrings.xml').findall('s:si', ns)]
            names = sorted(n for n in archive.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml', n))
            sheets, truncated = [], len(names) > 3
            for name in names[:3]:
                rows = []
                for row in safe_xml(archive, name).findall('.//s:sheetData/s:row', ns):
                    if len(rows) >= 100:
                        truncated = True
                        break
                    cells = {}
                    for cell in row.findall('s:c', ns):
                        letters = re.match(r'([A-Z]+)', cell.get('r', ''))
                        if not letters:
                            continue
                        col = 0
                        for c in letters[1]:
                            col = col * 26 + ord(c) - 64
                        if col > 20:
                            truncated = True
                            continue
                        value = cell.findtext('s:v', '', ns)
                        if cell.get('t') == 's':
                            value = strings[int(value)]
                        elif cell.get('t') == 'inlineStr':
                            value = ''.join(cell.find('s:is', ns).itertext())
                        truncated |= len(value) > 2000
                        cells[col - 1] = value[:2000]
                    rows.append([cells.get(i, '') for i in range(max(cells, default=-1) + 1)])
                sheets.append({'name': 'Hoja ' + re.search(r'sheet(\d+)', name)[1], 'rows': rows})
            return {'kind': 'table', 'sheets': sheets, 'truncated': truncated}
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError, RuntimeError, ValueError, IndexError, AttributeError, csv.Error):
        raise HTTPException(422, 'No se pudo generar la vista previa. Puedes descargar el archivo original.')
