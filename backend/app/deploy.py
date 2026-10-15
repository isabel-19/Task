"""Optional startup setup for hosts without a release command or interactive shell."""
import os
import subprocess
import sys
from pathlib import Path
from sqlalchemy import select
from . import models as m
from .db import SessionLocal
from .bootstrap import initialize


def prepare():
    if os.environ.get('RUN_MIGRATIONS', '').lower() == 'true':
        environment = os.environ.copy()
        if environment.get('MIGRATION_DATABASE_URL'):
            environment['DATABASE_URL'] = environment['MIGRATION_DATABASE_URL']
        subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'],
                       cwd=Path(__file__).resolve().parents[1], env=environment, check=True)
    email = os.environ.get('BOOTSTRAP_EMAIL', '').strip()
    password = os.environ.get('BOOTSTRAP_PASSWORD', '')
    if email or password:
        with SessionLocal() as db:
            if not db.scalar(select(m.User.id).limit(1)):
                initialize(db, os.environ.get('BOOTSTRAP_NAME', 'Jefatura OGC'), email, password)
                print('Cuenta inicial creada. Retira BOOTSTRAP_PASSWORD del alojamiento.')
