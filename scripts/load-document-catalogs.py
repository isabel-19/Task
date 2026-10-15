"""Load the register's existing destination dropdowns; do not import document rows."""
import argparse
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from sqlalchemy import select
from app.db import SessionLocal
from app import models as m
from app.service import audit
from app.security import permissions

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def recipient_catalog(source):
    names, references = {}, []
    with zipfile.ZipFile(source) as book:
        relations = {rel.attrib['Id']: rel.attrib['Target'] for rel in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        for sheet in ET.fromstring(book.read('xl/workbook.xml')).find('s:sheets', NS):
            title = sheet.attrib['name'].strip().lower()
            columns = {'F'} if title.startswith('8.1') else {'G'} if title.startswith(('8.2', '8.3', '8.4', '8.5')) else {'H', 'K'} if title.startswith('documentaci') else set()
            if not columns:
                continue
            target = relations[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            for rule in ET.fromstring(book.read(target)).findall('s:dataValidations/s:dataValidation', NS):
                areas = rule.attrib.get('sqref', '').split()
                if rule.attrib.get('type') != 'list' or not any(re.match(r'\$?([A-Z]+)', area)[1] in columns for area in areas):
                    continue
                formula = rule.findtext('s:formula1', namespaces=NS) or ''
                # Excel splits long inline lists into concatenated quoted strings.
                if not re.fullmatch(r'"(?:[^"]|"")*"(?:\s*&\s*"(?:[^"]|"")*")*', formula):
                    raise ValueError(f'Lista no admitida en {sheet.attrib["name"]}: {rule.attrib["sqref"]}')
                text = ''.join(part.replace('""', '"') for part in re.findall(r'"((?:[^"]|"")*)"', formula))
                for value in text.split(','):
                    value = ' '.join(value.split())
                    key = ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))
                    if value and len(value) <= 160:
                        names.setdefault(key, value)
                references.append({'sheet': sheet.attrib['name'], 'range': rule.attrib['sqref']})
    if not names:
        raise ValueError('El archivo no contiene listas de destinatarios reconocidas.')
    return {'recipients': sorted(names.values(), key=str.casefold), 'references': references}


def configure(source, preview):
    content = source.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    with SessionLocal.begin() as db:
        if db.scalar(select(m.ImportBatch.id).where(m.ImportBatch.entity == 'document-catalogs', m.ImportBatch.sha256 == digest)):
            return False
        actor = db.scalar(select(m.User).where(m.User.email == 'admin@example.invalid'))
        if not actor or 'admin.write' not in permissions(db, actor):
            raise RuntimeError('Se requiere administración local para configurar el catálogo.')
        backup = ROOT / 'backend/storage/imports' / (digest + '-document-catalogs.xlsx')
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_bytes(content)
        elif hashlib.sha256(backup.read_bytes()).hexdigest() != digest:
            raise RuntimeError('El respaldo del catálogo no coincide con la fuente.')
        batch = m.ImportBatch(filename=source.name, sheet='Destinatarios del registro documental', sha256=digest,
                              backup_path=backup.name, entity='document-catalogs', status='imported',
                              mapping={'scope': 'existing_dropdowns_only'}, preview=preview, modified_by=actor.id)
        db.add(batch)
        audit(db, actor, 'import-batches', batch, 'import_document_catalogs')
        return True


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    preview = recipient_catalog(args.source)
    created = configure(args.source, preview) if args.apply else False
    print(json.dumps({'options': len(preview['recipients']), 'validation_lists': len(preview['references']),
                      'catalog_created': created, 'sample': preview['recipients'][:8]}, ensure_ascii=False))
