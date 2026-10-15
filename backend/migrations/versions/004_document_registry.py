"""Add transactional numbering without changing existing documents or versions."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    folder = Path(__file__).resolve().parents[3] / 'database/migrations'
    filename = '004_document_registry.sql' if op.get_context().dialect.name == 'postgresql' else '004_document_registry_sqlite.sql'
    for statement in (folder / filename).read_text(encoding='utf-8').split(';'):
        if statement.strip():
            op.execute(text(statement))


def downgrade():
    raise RuntimeError('Restaura una copia verificada para conservar los correlativos asignados.')
