"""Grant the office chief the administrator's permissions, as requested."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    folder = Path(__file__).resolve().parents[3] / 'database/migrations'
    filename = '007_chief_administration.sql' if op.get_context().dialect.name == 'postgresql' else '007_chief_administration_sqlite.sql'
    for statement in (folder / filename).read_text(encoding='utf-8').split(';'):
        if statement.strip():
            op.execute(text(statement))


def downgrade():
    raise RuntimeError('Restaura una copia verificada antes de retirar permisos de administración a jefatura.')
