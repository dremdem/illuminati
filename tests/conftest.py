"""Shared test fixtures: app factory and async HTTP client."""

import httpx
import pytest

import ledger.main as main


@pytest.fixture
def app():  # type: ignore[no-untyped-def]
    """Create a fresh FastAPI app instance for testing."""
    return main.create_app()


@pytest.fixture
async def client(app):  # type: ignore[no-untyped-def]
    """
    Provide an async HTTP client wired to the test app.

    :param app: FastAPI application instance
    """
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
