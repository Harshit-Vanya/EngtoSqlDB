"""Pytest configuration and shared fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async test client for the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
