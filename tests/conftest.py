import pytest
from httpx import ASGITransport, AsyncClient

from ledger.main import create_app


@pytest.fixture
def app():  # type: ignore[no-untyped-def]
    """Create a fresh FastAPI app instance for testing."""
    return create_app()


@pytest.fixture
async def client(app):  # type: ignore[no-untyped-def]
    """
    Provide an async HTTP client wired to the test app.

    :param app: FastAPI application instance
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
