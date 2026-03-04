"""Shared fixtures for integration tests: testcontainers and sessions."""

import collections.abc

import alembic.command
import alembic.config
import pytest
import sqlalchemy.ext.asyncio as sa_async
import sqlalchemy.pool as sa_pool
import testcontainers.postgres


@pytest.fixture(scope="session")
def pg_container() -> collections.abc.Generator[
    testcontainers.postgres.PostgresContainer, None, None
]:
    """
    Start a PostgreSQL container for the test session.

    :return: running PostgreSQL testcontainer
    """
    with testcontainers.postgres.PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def sync_database_url(pg_container: testcontainers.postgres.PostgresContainer) -> str:
    """
    Build a synchronous database URL from the running container.

    :param pg_container: running PostgreSQL testcontainer
    :return: sync connection string for Alembic
    """
    return pg_container.get_connection_url()


@pytest.fixture(scope="session")
def async_database_url(sync_database_url: str) -> str:
    """
    Build an async database URL by swapping the driver to asyncpg.

    :param sync_database_url: sync connection string
    :return: async connection string for SQLAlchemy
    """
    return sync_database_url.replace("psycopg2", "asyncpg")


@pytest.fixture(scope="session")
def _run_migrations(sync_database_url: str) -> None:
    """
    Apply Alembic migrations to the test database.

    :param sync_database_url: sync connection string for Alembic
    """
    cfg = alembic.config.Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", sync_database_url)
    alembic.command.upgrade(cfg, "head")


@pytest.fixture(scope="session")
def async_engine(
    async_database_url: str,
    _run_migrations: None,
) -> collections.abc.Generator[sa_async.AsyncEngine, None, None]:
    """
    Create an async engine connected to the test database.

    :param async_database_url: async connection string
    :param _run_migrations: ensures migrations run before engine is used
    :return: async SQLAlchemy engine
    """
    engine = sa_async.create_async_engine(
        async_database_url,
        poolclass=sa_pool.NullPool,
    )
    yield engine


@pytest.fixture
async def db_session(
    async_engine: sa_async.AsyncEngine,
) -> collections.abc.AsyncGenerator[sa_async.AsyncSession, None]:
    """
    Provide a per-test async session that rolls back after the test.

    Tests use ``flush()`` to push data to the database within the session's
    implicit transaction. The ``rollback()`` at the end undoes everything,
    giving each test a clean slate.

    :param async_engine: session-scoped async engine
    :return: yields an async session that rolls back after the test
    """
    session = sa_async.AsyncSession(
        bind=async_engine,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        await session.rollback()
        await session.close()
