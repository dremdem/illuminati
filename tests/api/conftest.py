"""API test configuration: override app to use the test database session."""

import collections.abc

import httpx
import pytest
import sqlalchemy.ext.asyncio as sa_async

import ledger.api.dependencies as dependencies
import ledger.main as main


@pytest.fixture
def app(
    db_session: sa_async.AsyncSession,
) -> main.fastapi.FastAPI:
    """
    Create a FastAPI app wired to the test database session.

    Overrides the ``get_session`` dependency so all requests use the
    per-test session that rolls back after the test.

    :param db_session: per-test async session with automatic rollback
    :return: FastAPI app configured for testing
    """
    application = main.create_app()

    async def _override_get_session() -> collections.abc.AsyncGenerator[
        sa_async.AsyncSession, None
    ]:
        """
        Yield the test session without commit/rollback (handled by fixture).

        :return: yields the test database session
        """
        yield db_session

    application.dependency_overrides[dependencies.get_session] = _override_get_session
    return application


@pytest.fixture
async def client(
    app: main.fastapi.FastAPI,
) -> collections.abc.AsyncGenerator[httpx.AsyncClient, None]:
    """
    Provide an async HTTP client wired to the test app.

    :param app: FastAPI application instance with test DB
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
