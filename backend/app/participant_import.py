"""Read ROADMAP people columns without importing tasks or inferring real emails."""
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
import hashlib
import io
import json
import posixpath
import re
import secrets
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from sqlalchemy import select
from . import models as m
from .security import hash_password
from .service import audit

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
PERSON_HEADERS = {'participantes', 'responsable de la actividad', 'responsable',
                  'resposable', 'apoyo', 'elaborado por', 'team ogc', 'nombre'}
NON_PEOPLE = {'todo el equipo', 'todos', 'equipo', 'equipo ogc', 'ogc', 'por asignar',
              'pendiente', 'n/a', 'na', '-', 'avanza', 'conecta'}
IMPORT_SHEET = 'Participantes (todas las hojas)'


def person_key(value):
    value = ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c))
    return ' '.join(value.casefold().strip(' :').split())


def parse_participants(filename, data):
    if Path(filename).suffix.lower() != '.xlsx':
        raise ValueError('Usa el libro ROADMAP en formato XLSX.')
    names, ignored = {}, []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(info.file_size for info in archive.infolist()) > 150_000_000:
            raise ValueError('El libro excede el límite de lectura.')
        def xml(path):
            raw = archive.read(path)
            if b'<!DOCTYPE' in raw:
                raise ValueError('No se admiten XML con DTD.')
            return ET.fromstring(raw)
        shared = [''.join(t.text or '' for t in item.iter('{'+NS['s']+'}t'))
                  for item in xml('xl/sharedStrings.xml')] if 'xl/sharedStrings.xml' in archive.namelist() else []
        rels = {r.get('Id'): r.get('Target') for r in xml('xl/_rels/workbook.xml.rels')}
        sheets = list(xml('xl/workbook.xml').find('s:sheets', NS))
        for sheet in sheets:
            target = rels[sheet.get('{'+NS['r']+'}id')]
            path = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            rows = []
            for row in xml(path).findall('s:sheetData/s:row', NS):
                cells = {}
                for cell in row:
                    node = cell.find('s:v', NS)
                    value = node.text or '' if node is not None else ''
                    if cell.get('t') == 's':
                        value = shared[int(value)] if value else ''
                    elif cell.get('t') == 'inlineStr':
                        value = ''.join(t.text or '' for t in cell.iter('{'+NS['s']+'}t'))
                    if value.strip():
                        cells[cell.get('r')] = value.strip()
                if cells:
                    rows.append((int(row.get('r')), cells))
            columns = {}
            for number, cells in rows:
                if number > 4:
                    break
                for cell, value in cells.items():
                    if person_key(value) in PERSON_HEADERS:
                        columns[re.sub(r'\d', '', cell)] = (number, value)
            for number, cells in rows:
                for cell, value in cells.items():
                    column = re.sub(r'\d', '', cell)
                    if column not in columns or number <= columns[column][0]:
                        continue
                    reference = {'sheet': sheet.get('name'), 'cell': cell, 'row': number,
                                 'column_heading': columns[column][1], 'original': value}
                    if person_key(value) in NON_PEOPLE:
                        ignored.append(reference | {'reason': 'Grupo u organización, no una persona.'})
                        continue
                    for token in re.split(r'[/,;\n&]+|\s+y\s+', value, flags=re.I):
                        token = ' '.join(token.strip(' .•-').split())
                        key = person_key(token)
                        if not key:
                            continue
                        if key in NON_PEOPLE or len(token) > 80 or len(token) < 2 or any(c.isdigit() for c in token):
                            ignored.append(reference | {'token': token, 'reason': 'Valor no identificable como persona.'})
                            continue
                        item = names.setdefault(key, {'key': key, 'forms': Counter(), 'references': []})
                        item['forms'][token] += 1
                        item['references'].append(reference)
    people = []
    for key, item in sorted(names.items()):
        # Accent/case variants are equivalent. Different spellings remain separate identities.
        forms = list(item['forms'])
        accented = [f for f in forms if any(unicodedata.combining(c) for c in unicodedata.normalize('NFD', f))]
        selected = max(accented or forms, key=lambda f: item['forms'][f])
        name = selected.title() if selected.isupper() or selected.islower() else selected
        possible = sorted(other for other in names if other != key and
                          (SequenceMatcher(None, key, other).ratio() >= 0.78 or
                           (min(len(key), len(other)) >= 3 and (key.startswith(other) or other.startswith(key)))))
        people.append({'key': key, 'name': name, 'aliases': sorted(forms),
                       'possible_variants': possible, 'references': item['references']})
    return {'kind': 'roadmap_participants', 'filename': Path(filename).name,
            'sha256': hashlib.sha256(data).hexdigest(), 'sheet_count': len(sheets),
            'people': people, 'ignored': ignored}


def local_identifier(key):
    slug = re.sub(r'[^a-z0-9]+', '-', key).strip('-')[:100] or 'participante'
    return slug + '-' + hashlib.sha256(key.encode()).hexdigest()[:6] + '@participantes.invalid'


def imported_people(db):
    result = {}
    for batch in db.scalars(select(m.ImportBatch).where(m.ImportBatch.entity == 'users', m.ImportBatch.status == 'imported')):
        if batch.preview.get('kind') == 'roadmap_participants':
            for person in batch.preview.get('people', []):
                if person.get('user_id'):
                    result[person['user_id']] = person
    return result


def register_participants(db, actor, manifest, data, storage, credentials_path):
    existing_batch = db.scalar(select(m.ImportBatch).where(m.ImportBatch.sha256 == manifest['sha256'],
                                                          m.ImportBatch.entity == 'users', m.ImportBatch.sheet == IMPORT_SHEET))
    if existing_batch:
        return {'created': 0, 'reused': len(existing_batch.preview['people']), 'batch_id': existing_batch.id, 'already_imported': True}
    if not manifest['people']:
        raise ValueError('No se encontraron participantes en las columnas reconocidas.')
    if hashlib.sha256(data).hexdigest() != manifest['sha256']:
        raise ValueError('La fuente cambió después de la lectura.')
    member_role = db.scalar(select(m.Role).where(m.Role.name == 'integrante'))
    if not member_role:
        raise ValueError('Configura el rol integrante antes de registrar participantes.')
    storage = Path(storage); storage.mkdir(parents=True, exist_ok=True)
    backup = storage / (manifest['sha256'] + '-participants.xlsx')
    if backup.exists():
        if hashlib.sha256(backup.read_bytes()).hexdigest() != manifest['sha256']:
            raise ValueError('El respaldo existente no coincide con el original.')
    else:
        backup.write_bytes(data)
    credentials_path = Path(credentials_path)
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials = json.loads(credentials_path.read_text(encoding='utf-8')) if credentials_path.exists() else {'notice': 'Accesos locales. Los identificadores @participantes.invalid no son correos institucionales. No publicar este archivo.', 'accounts': {}}
    previous_people = imported_people(db)
    prior_by_key = {p['key']: identifier for identifier, p in previous_people.items()}
    users = list(db.scalars(select(m.User)))
    created = reused = 0
    for person in manifest['people']:
        matching = [user for user in users if person_key(user.name) == person['key']]
        user = db.get(m.User, prior_by_key[person['key']]) if person['key'] in prior_by_key else None
        if user is None:
            user = next((u for u in users if u.email == local_identifier(person['key'])), None)
        if user is None and len(matching) == 1:
            user = matching[0]
        if user is None and len(matching) > 1:
            raise ValueError('Hay más de una cuenta para '+person['name']+'. Resuelve esa identidad antes de importar.')
        if user is None:
            password = secrets.token_urlsafe(20)
            user = m.User(name=person['name'], email=local_identifier(person['key']), password_hash=hash_password(password),
                          active=True, department='ROADMAP', modified_by=actor.id)
            db.add(user); audit(db, actor, 'users', user, 'import_participant')
            assignment = m.UserRole(user_id=user.id, role_id=member_role.id, modified_by=actor.id)
            db.add(assignment); audit(db, actor, 'user-roles', assignment, 'import_participant')
            users.append(user)
            credentials['accounts'][user.id] = {'name': user.name, 'identifier': user.email, 'password': password, 'role': 'integrante'}
            created += 1
        else:
            reused += 1
        person['user_id'] = user.id
    batch = m.ImportBatch(filename=manifest['filename'], sha256=manifest['sha256'], sheet=IMPORT_SHEET,
                          backup_path=backup.name, entity='users', status='imported',
                          mapping={'headers': sorted(PERSON_HEADERS), 'normalization': 'case_and_accents_only',
                                   'contact_emails': 'not_supplied', 'scope': 'participants_only'},
                          preview=manifest, modified_by=actor.id)
    db.add(batch); audit(db, actor, 'import-batches', batch, 'register_participants')
    # Write access material before commit so a file error cannot silently create inaccessible accounts.
    temporary = credentials_path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(credentials, ensure_ascii=False, indent=2), encoding='utf-8')
    db.commit()
    temporary.replace(credentials_path)
    return {'created': created, 'reused': reused, 'batch_id': batch.id, 'already_imported': False}
