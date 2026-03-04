"""Alembic migration environment configuration."""

import logging.config
import os

import alembic.context as alembic_context
import sqlalchemy
import sqlalchemy.pool as pool

import ledger.infrastructure.database as database
import ledger.infrastructure.models as orm_models  # noqa: F401 — register models with Base

config = alembic_context.config

if config.config_file_name is not None:
    logging.config.fileConfig(config.config_file_name)

# Use DATABASE_URL env var only when sqlalchemy.url is not already set
# (tests pass the URL programmatically via config.set_main_option)
existing_url = config.get_main_option("sqlalchemy.url")
if not existing_url:
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        # Alembic needs sync driver; swap asyncpg -> psycopg2 for migrations
        sync_url = database_url.replace("+asyncpg", "")
        config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = database.Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in offline mode using a URL instead of a live connection.

    :return: None
    """
    url = config.get_main_option("sqlalchemy.url")
    alembic_context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with alembic_context.begin_transaction():
        alembic_context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in online mode using a live database connection.

    :return: None
    """
    connectable = sqlalchemy.engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        alembic_context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with alembic_context.begin_transaction():
            alembic_context.run_migrations()


if alembic_context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
