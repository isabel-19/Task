"""Private files attached to task contributions."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    folder = Path(__file__).resolve().parents[3] / 'database/migrations'
    filename = '008_evidence_files.sql' if op.get_context().dialect.name == 'postgresql' else '008_evidence_files_sqlite.sql'
    for statement in (folder / filename).read_text(encoding='utf-8').split(';'):
        if statement.strip():
            op.execute(text(statement))


def downgrade():
    raise RuntimeError('Respalda los archivos y su base antes de retirar el almacenamiento de evidencias.')
