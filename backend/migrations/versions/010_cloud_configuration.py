"""Central encrypted provider registration for all authorized users."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    folder = Path(__file__).resolve().parents[3] / 'database/migrations'
    name = '010_cloud_configuration.sql' if op.get_context().dialect.name == 'postgresql' else '010_cloud_configuration_sqlite.sql'
    for statement in (folder / name).read_text(encoding='utf-8').split(';'):
        if statement.strip():
            op.execute(text(statement))


def downgrade():
    raise RuntimeError('Verifica un respaldo antes de retirar la configuración de conexiones.')
