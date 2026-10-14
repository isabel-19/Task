"""Preserve existing records while adding authorship, evidence and chief reviews."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    path = Path(__file__).resolve().parents[3] / 'database/migrations'
    name = '002_task_collaboration.sql' if op.get_context().dialect.name == 'postgresql' else '002_task_collaboration_sqlite.sql'
    for statement in (path / name).read_text(encoding='utf-8').split(';'):
        if statement.strip():
            op.execute(text(statement))


def downgrade():
    raise RuntimeError('Esta migración conserva el historial. Restaura una copia verificada para retroceder.')
