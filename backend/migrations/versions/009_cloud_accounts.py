"""Encrypted per-user Google and Microsoft connections."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    folder = Path(__file__).resolve().parents[3] / 'database/migrations'
    name = '009_cloud_accounts.sql' if op.get_context().dialect.name == 'postgresql' else '009_cloud_accounts_sqlite.sql'
    for statement in (folder / name).read_text(encoding='utf-8').split(';'):
        if statement.strip(): op.execute(text(statement))


def downgrade():
    raise RuntimeError('Desvincula las cuentas y verifica un respaldo antes de retirar las conexiones.')
