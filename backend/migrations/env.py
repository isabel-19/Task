from alembic import context
from sqlalchemy import create_engine, pool
from app.db import Base
from app.config import settings
from app import models

config = context.config
if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=Base.metadata, literal_binds=True, dialect_opts={'paramstyle':'named'})
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(settings.database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        if engine.dialect.name == 'sqlite':
            connection.exec_driver_sql('PRAGMA foreign_keys=ON')
            connection.commit()
        if engine.dialect.name == 'postgresql':
            connection.exec_driver_sql('CREATE SCHEMA IF NOT EXISTS roadmap')
            connection.commit()
        context.configure(connection=connection, target_metadata=Base.metadata,
                          version_table_schema='roadmap' if engine.dialect.name == 'postgresql' else None)
        with context.begin_transaction():
            context.run_migrations()
