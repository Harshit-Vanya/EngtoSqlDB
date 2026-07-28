"""Test the health endpoint (Phase 0 verification)."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health endpoint should return 200 with status info."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert "version" in data["data"]
