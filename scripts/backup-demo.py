"""Consistent local SQLite backup; never print database content or credentials."""
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

root = Path(__file__).resolve().parents[1]
source = root / 'backend/roadmap-demo.db'
folder = root / '.local/backups'
folder.mkdir(parents=True, exist_ok=True)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
destination = folder / f'roadmap-demo-{stamp}.db'
if not source.is_file():
    raise SystemExit('No existe la base local de demostración.')
with sqlite3.connect(f'file:{source.as_posix()}?mode=ro', uri=True) as original, sqlite3.connect(destination) as backup:
    original.backup(backup)
    if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise SystemExit('El respaldo falló la comprobación de integridad.')
checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
destination.with_suffix('.json').write_text(json.dumps({'source':source.name,'backup':destination.name,'sha256':checksum,'created_at':stamp},indent=2),encoding='utf-8')
print('Respaldo verificado en .local/backups/' + destination.name)
