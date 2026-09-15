from logging.config import fileConfig

from alembic import context
from flask import current_app


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_metadata():
    """Obtiene los metadatos de SQLAlchemy registrados por Flask-Migrate."""
    database = current_app.extensions['migrate'].db
    return database.metadatas[None] if hasattr(database, 'metadatas') else database.metadata


def run_migrations_offline():
    context.configure(
        url=current_app.config['SQLALCHEMY_DATABASE_URI'].render_as_string(hide_password=False),
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = current_app.extensions['migrate'].db.engine
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=get_metadata())
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
