"""Read the reference register; optionally initialize counters without importing its documents."""
import argparse
import json
import re
import sys
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from sqlalchemy import case, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from app.db import SessionLocal
from app import models as m
from app.document_registry import SERIES, series_key, format_number

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def register_numbers(source):
    counters = {}
    with zipfile.ZipFile(source) as book:
        strings = [''.join(node.itertext()) for node in ET.fromstring(book.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in book.namelist() else []
        relations = {rel.attrib['Id']: rel.attrib['Target'] for rel in ET.fromstring(book.read('xl/_rels/workbook.xml.rels'))}
        for sheet in ET.fromstring(book.read('xl/workbook.xml')).find('s:sheets', NS):
            name = ''.join(c for c in unicodedata.normalize('NFD', sheet.attrib['name']) if not unicodedata.combining(c)).lower()
            if not re.match(r'\s*8\.', name):
                continue
            key = next((key for keyword, key in [('tecnic', 'informe-tecnico'), ('cartas simples', 'carta'),
                       ('cartas multiples', 'carta-multiple'), ('informes enviados', 'informe'),
                       ('oficios', 'oficio'), ('actas', 'acta')] if keyword in name), None)
            if not key:
                continue
            target = relations[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target = target.lstrip('/') if target.startswith('/') else 'xl/' + target
            for row in ET.fromstring(book.read(target)).findall('s:sheetData/s:row', NS):
                cells = {}
                for cell in row:
                    value = cell.find('s:v', NS)
                    text = value.text if value is not None else ''.join(cell.find('s:is', NS).itertext()) if cell.find('s:is', NS) is not None else ''
                    if cell.attrib.get('t') == 's':
                        text = strings[int(text)]
                    cells[re.sub(r'\d+', '', cell.attrib['r'])] = text
                # Blank, pre-numbered rows do not mean an issued document.
                if not cells.get('D', '').strip() or cells.get('D', '').strip() in {'0', '1.0'}:
                    continue
                match = re.search(r'N[°ºª.]?\s*(\d+)\s*[-–—]\s*(\d{4})', cells.get('C', ''), re.I)
                if match:
                    number, year = map(int, match.groups())
                    counters[key, year] = max(counters.get((key, year), 0), number)
    if not counters:
        raise ValueError('No se encontraron series de documentos emitidos en las hojas de referencia.')
    return counters


def configure(counters):
    with SessionLocal.begin() as db:
        present = {series_key(name) for name in db.scalars(select(m.DocumentType.name))}
        for series, _ in counters:
            if series not in present:
                db.add(m.DocumentType(name=SERIES[series][0]))
                present.add(series)
        insert = postgres_insert if db.get_bind().dialect.name == 'postgresql' else sqlite_insert
        table = m.DocumentSequence.__table__
        for (series, year), floor in counters.items():
            statement = insert(table).values(series=series, year=year, last_number=floor)
            db.execute(statement.on_conflict_do_update(
                index_elements=[table.c.series, table.c.year],
                set_={'last_number': case((table.c.last_number > floor, table.c.last_number), else_=floor)},
            ))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--apply', action='store_true', help='Inicializar correlativos; ejecutar migraciones antes.')
    args = parser.parse_args()
    counters = register_numbers(args.source)
    if args.apply:
        configure(counters)
    print(json.dumps({'applied': args.apply, 'series': [
        {'type': SERIES[key][0], 'year': year, 'last_in_reference': number,
         'reference_next': format_number(key, year, number + 1)}
        for (key, year), number in sorted(counters.items())
    ]}, ensure_ascii=False, indent=2))
