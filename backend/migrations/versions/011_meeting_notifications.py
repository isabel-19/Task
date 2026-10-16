"""Meeting invitations and change notices for attendees."""
from pathlib import Path
from alembic import op
from sqlalchemy import text

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    folder = Path(__file__).resolve().parents[3] / 'database/migrations'
    postgres = op.get_context().dialect.name == 'postgresql'
    name = '011_meeting_notifications.sql' if postgres else '011_meeting_notifications_sqlite.sql'
    for statement in (folder / name).read_text(encoding='utf-8').split(';'):
        if statement.strip():
            op.execute(text(statement))
    if postgres:
        # The application role exists only on hosted Postgres; grant to it when present.
        has_role = op.get_bind().execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'roadmap_api'")).scalar()
        if has_role:
            op.execute(text('GRANT SELECT, INSERT, UPDATE ON roadmap.notifications TO roadmap_api'))


def downgrade():
    raise RuntimeError('Verifica un respaldo antes de retirar los avisos de reuniones.')
