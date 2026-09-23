# tests/test_health.py
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint returns ok and confirms DB is reachable."""
    response = await client.get("/api/v1/health/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    """Root endpoint returns a welcome message."""
    response = await client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "Welcome" in data["message"]


@pytest.mark.asyncio
async def test_health_database_unreachable(client, monkeypatch):
    """If DB query fails, /health should report degraded."""
    from sqlalchemy.ext.asyncio import AsyncSession

    async def broken_execute(self, *args, **kwargs):
        raise Exception("DB is down")

    monkeypatch.setattr(AsyncSession, "execute", broken_execute)

    response = await client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "unreachable"