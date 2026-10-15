"""Record dispatch and follow-up fields from the original workbook."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    folder = Path(__file__).resolve().parents[3] / 'database/migrations'
    filename = '006_document_workflow.sql' if op.get_context().dialect.name == 'postgresql' else '006_document_workflow_sqlite.sql'
    for statement in (folder / filename).read_text(encoding='utf-8').split(';'):
        if statement.strip():
            op.execute(text(statement))


def downgrade():
    raise RuntimeError('Restaura una copia verificada para conservar el seguimiento documental.')
