"""Smoke test for the health check endpoint."""

import httpx
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client: httpx.AsyncClient) -> None:
    """Verify health endpoint returns 200 with status ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
