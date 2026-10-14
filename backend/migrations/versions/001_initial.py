"""Initial schema from frozen SQL, generated and reviewed with SQLAlchemy 2."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    dialect = op.get_context().dialect.name
    path = Path(__file__).resolve().parents[3] / 'database/migrations'
    filename = '001_initial.sql' if dialect == 'postgresql' else '001_initial_sqlite.sql'
    sql = (path / filename).read_text(encoding='utf-8')
    for statement in sql.split(';'):
        if statement.strip():
            op.execute(text(statement))


def downgrade():
    raise RuntimeError('La migración inicial no se elimina automáticamente. Restaura una copia verificada en una instancia vacía.')
