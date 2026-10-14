"""Simplify task input while preserving existing task/project relationships."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    folder=Path(__file__).resolve().parents[3]/'database/migrations'
    name='003_task_form.sql' if op.get_context().dialect.name=='postgresql' else '003_task_form_sqlite.sql'
    for statement in (folder/name).read_text(encoding='utf-8').split(';'):
        if statement.strip():op.execute(text(statement))


def downgrade():
    raise RuntimeError('Restaura una copia verificada para conservar las relaciones e historial.')
