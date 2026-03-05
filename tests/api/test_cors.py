"""API tests for CORS middleware configuration."""

import httpx
import pytest


@pytest.mark.asyncio
async def test_cors_allows_configured_origin(client: httpx.AsyncClient) -> None:
    """Preflight request from allowed origin returns CORS headers."""
    response = await client.options(
        "/api/accounts",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.mark.asyncio
async def test_cors_allows_second_configured_origin(
    client: httpx.AsyncClient,
) -> None:
    """Preflight request from second allowed origin returns CORS headers."""
    response = await client.options(
        "/api/accounts",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_cors_blocks_unknown_origin(client: httpx.AsyncClient) -> None:
    """Preflight request from unknown origin does not return allow header."""
    response = await client.options(
        "/api/accounts",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_cors_simple_get_includes_headers(client: httpx.AsyncClient) -> None:
    """Simple GET with Origin header includes CORS response headers."""
    response = await client.get(
        "/api/accounts",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
