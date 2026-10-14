"""Local, explicit enrollment. Keep source names and credentials out of Git."""
import argparse
import json
from pathlib import Path
import sys
import os
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
parser=argparse.ArgumentParser()
parser.add_argument('--source',required=True)
parser.add_argument('--apply',action='store_true')
arguments=parser.parse_args()
source=Path(arguments.source).resolve()
os.chdir(root/'backend')
from sqlalchemy import select
from app import models as m
from app.db import SessionLocal
from app.security import permissions
from app.participant_import import parse_participants, register_participants

data=source.read_bytes()
manifest=parse_participants(source.name,data)
folder=root/'.local/qa';folder.mkdir(parents=True,exist_ok=True)
(folder/'participant-preview.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'people':len(manifest['people']),'names':[p['name'] for p in manifest['people']],
                  'possible_variants':{p['name']:p['possible_variants'] for p in manifest['people'] if p['possible_variants']},
                  'sheets':manifest['sheet_count']},ensure_ascii=False))
if arguments.apply:
    with SessionLocal() as db:
        actor=db.scalar(select(m.User).where(m.User.email=='admin@example.invalid'))
        if not actor or 'admin.write' not in permissions(db,actor):
            raise SystemExit('Se requiere la cuenta administradora local para esta importación.')
        result=register_participants(db,actor,manifest,data,root/'backend/storage/imports',root/'.local/participants-access.json')
    print(json.dumps(result,ensure_ascii=False))
    access=json.loads((root/'.local/participants-access.json').read_text(encoding='utf-8'))
    lines=[access['notice'],'']
    for account in sorted(access['accounts'].values(),key=lambda a:a['name']):
        lines.extend(['Nombre: '+account['name'], 'Identificador local: '+account['identifier'],
                      'Contraseña: '+account['password'], 'Rol: '+account['role'], ''])
    (root/'.local/participantes-accesos.txt').write_text('\n'.join(lines),encoding='utf-8')
    print('Credenciales locales guardadas en .local/participants-access.json. No se imprimen contraseñas.')
