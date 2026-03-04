"""Async database engine, session factory, and SQLAlchemy declarative base."""

import typing

import sqlalchemy.ext.asyncio as sa_async
import sqlalchemy.orm as orm


class Base(orm.DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def create_async_engine(
    database_url: str,
    echo: bool = False,
) -> sa_async.AsyncEngine:
    """
    Create an async SQLAlchemy engine.

    :param database_url: PostgreSQL connection string (asyncpg driver)
    :param echo: if True, log all SQL statements
    :return: configured async engine
    """
    return sa_async.create_async_engine(database_url, echo=echo)


def create_async_session_factory(
    engine: sa_async.AsyncEngine,
) -> sa_async.async_sessionmaker[sa_async.AsyncSession]:
    """
    Create an async session factory bound to the given engine.

    :param engine: async SQLAlchemy engine
    :return: async session factory
    """
    return sa_async.async_sessionmaker(
        engine,
        expire_on_commit=False,
    )


async def get_db(
    session_factory: sa_async.async_sessionmaker[sa_async.AsyncSession],
) -> typing.AsyncGenerator[sa_async.AsyncSession, None]:
    """
    Provide an async database session as a FastAPI dependency.

    Commits on success, rolls back on exception, always closes.

    :param session_factory: async session factory
    :return: yields an async session
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
