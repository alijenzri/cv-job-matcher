"""
Test fixtures for CV-Job Matcher API tests.
Uses httpx AsyncClient for async endpoint testing.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    """Synchronous test client for simple tests."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    """Async test client for async endpoint tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
