"""Generate the initial SQL before freezing it; never regenerate deployed migrations."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from sqlalchemy import create_mock_engine
from app.db import Base
from app import models

folder = Path(__file__).resolve().parents[1] / 'database/migrations'
folder.mkdir(parents=True, exist_ok=True)
for dialect, name in [('postgresql', '001_initial.sql'), ('sqlite', '001_initial_sqlite.sql')]:
    statements = []
    for table in Base.metadata.tables.values():
        table.schema = 'roadmap' if dialect == 'postgresql' else None
    if dialect == 'postgresql':
        statements.append('CREATE SCHEMA IF NOT EXISTS roadmap;')
    def collect(sql, *args, **kwargs):
        statements.append(str(sql.compile(dialect=engine.dialect)).strip() + ';')
    engine = create_mock_engine(f'{dialect}://', collect)
    Base.metadata.create_all(engine)
    (folder / name).write_text('-- ROADMAP OGC · esquema inicial congelado\n-- Aplicar mediante alembic upgrade head.\n\n' + '\n\n'.join(statements) + '\n', encoding='utf-8')
    print(f'{name}: {len(Base.metadata.tables)} tablas; {len(statements)} sentencias')
