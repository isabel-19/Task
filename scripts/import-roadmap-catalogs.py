"""Read Excel labels for dropdowns; do not import tasks or terminal statuses."""
from pathlib import Path
import argparse, hashlib, json, os, posixpath, re, sys, zipfile
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--apply',action='store_true')
args=parser.parse_args();source=Path(args.source).resolve();data=source.read_bytes()
os.chdir(root/'backend');sys.path.insert(0,str(root/'backend'))
from sqlalchemy import select
from app import models as m
from app.db import SessionLocal
from app.participant_import import NS, person_key
from app.security import permissions
from app.service import audit

themes={};office_lines=[]
with zipfile.ZipFile(source) as z:
    def xml(path):
        raw=z.read(path)
        if b'<!DOCTYPE' in raw:raise ValueError('No se admiten DTD.')
        return ET.fromstring(raw)
    strings=[''.join(t.text or '' for t in x.iter('{'+NS['s']+'}t')) for x in xml('xl/sharedStrings.xml')] if 'xl/sharedStrings.xml' in z.namelist() else []
    rels={r.get('Id'):r.get('Target') for r in xml('xl/_rels/workbook.xml.rels')}
    for sheet in xml('xl/workbook.xml').find('s:sheets',NS):
        target=rels[sheet.get('{'+NS['r']+'}id')];path=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        rows=[];columns={}
        for row in xml(path).findall('s:sheetData/s:row',NS):
            values={}
            for c in row:
                v=c.find('s:v',NS);value=v.text or '' if v is not None else ''
                if c.get('t')=='s':value=strings[int(value)] if value else ''
                elif c.get('t')=='inlineStr':value=''.join(t.text or '' for t in c.iter('{'+NS['s']+'}t'))
                if value.strip():values[c.get('r')]=value.strip()
            number=int(row.get('r'));rows.append((number,values))
            if number<=4:
                for address,value in values.items():
                    normalized=person_key(value)
                    if normalized in {'ejes tematicos','tematica','oficina donde se encuentra'}:
                        columns[re.sub(r'\d','',address)]=(number,normalized)
        for number,values in rows:
            for address,value in values.items():
                column=re.sub(r'\d','',address)
                if column not in columns or number<=columns[column][0]:continue
                ref={'sheet':sheet.get('name'),'cell':address,'original':value}
                if columns[column][1]=='oficina donde se encuentra':office_lines.append(ref)
                else:
                    name=' '.join(value.split());key=person_key(name)
                    if name and len(name)<=160:
                        themes.setdefault(key,{'name':name,'references':[]})['references'].append(ref)
offices={}
for ref in office_lines:
    for line in ref['original'].splitlines():
        name=re.sub(r'^\s*\d{1,2}/\d{1,2}\s*','',line).strip()
        if name and re.fullmatch(r'[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+',name) and len(name.split())<=3:
            offices.setdefault(person_key(name),{'name':name.capitalize(),'references':[]})
for key,office in offices.items():
    office['references']=[ref for ref in office_lines if re.search(r'\b'+re.escape(key)+r'\b',person_key(ref['original']))]
manifest={'kind':'roadmap_task_catalogs','sha256':hashlib.sha256(data).hexdigest(), 'themes':list(themes.values()),'offices':sorted(offices.values(),key=lambda o:o['name'])}
out=root/'.local/qa/task-catalog-preview.json';out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'themes':len(themes),'theme_names':[v['name'] for v in themes.values()],'offices':[v['name'] for v in offices.values()]},ensure_ascii=False))
if args.apply:
    with SessionLocal() as db:
        existing=db.scalar(select(m.ImportBatch).where(m.ImportBatch.sha256==manifest['sha256'],m.ImportBatch.entity=='task-catalogs'))
        if existing:print('Los catálogos ya estaban registrados; no se duplicaron.')
        else:
            actor=db.scalar(select(m.User).where(m.User.email=='admin@example.invalid'))
            if not actor or 'admin.write' not in permissions(db,actor):raise RuntimeError('Se requiere administración local.')
            axes=list(db.scalars(select(m.Axis)))
            for item in manifest['themes']:
                axis=next((a for a in axes if person_key(a.name)==person_key(item['name'])),None)
                if not axis:
                    axis=m.Axis(name=item['name'],modified_by=actor.id);db.add(axis);audit(db,actor,'axes',axis,'import_task_theme');axes.append(axis)
                item['axis_id']=axis.id
            backup=root/'backend/storage/imports'/(manifest['sha256']+'-form-catalogs.xlsx')
            backup.parent.mkdir(parents=True,exist_ok=True)
            if backup.exists() and hashlib.sha256(backup.read_bytes()).hexdigest()!=manifest['sha256']:raise RuntimeError('El respaldo no coincide.')
            if not backup.exists():backup.write_bytes(data)
            batch=m.ImportBatch(filename=source.name,sha256=manifest['sha256'],sheet='Temáticas y oficinas',backup_path=backup.name,entity='task-catalogs',status='imported',mapping={'scope':'dropdown_labels_only'},preview=manifest,modified_by=actor.id)
            db.add(batch);audit(db,actor,'import-batches',batch,'import_task_catalogs');db.commit()
            print('Temáticas y oficinas registradas para los desplegables.')
