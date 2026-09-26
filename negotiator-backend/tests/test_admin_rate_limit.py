# tests/test_admin_rate_limit.py
"""
Tests for admin registration gates: feature flag, secret code, rate limit.
"""
import pytest

from app.core.rate_limit import admin_register_limiter
from app.core.config import settings


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Clear the rate limiter before each test."""
    admin_register_limiter.reset()
    yield
    admin_register_limiter.reset()


def _payload(email, code=None):
    body = {
        "email": email,
        "password": "AdminPass123",
        "name": "Rate Admin",
        "consent_given": True,
    }
    if code is not None:
        body["registration_code"] = code
    return body


@pytest.mark.asyncio
async def test_admin_register_within_limit(client):
    """First 5 registrations go through."""
    for i in range(5):
        r = await client.post(
            "/api/v1/auth/register/admin",
            json=_payload(f"admin-{i}@negotiator-ai.com"),
        )
        assert r.status_code == 201, f"attempt {i}: {r.text}"


@pytest.mark.asyncio
async def test_admin_register_rate_limited(client):
    """6th registration from the same IP returns 429."""
    for i in range(5):
        await client.post(
            "/api/v1/auth/register/admin",
            json=_payload(f"rate-{i}@negotiator-ai.com"),
        )

    r = await client.post(
        "/api/v1/auth/register/admin",
        json=_payload("rate-6@negotiator-ai.com"),
    )
    assert r.status_code == 429
    assert "too many" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_register_disabled_by_flag(client, monkeypatch):
    """When ADMIN_REGISTRATION_ENABLED=False, endpoint returns 403."""
    monkeypatch.setattr(settings, "ADMIN_REGISTRATION_ENABLED", False)

    r = await client.post(
        "/api/v1/auth/register/admin",
        json=_payload("disabled@negotiator-ai.com"),
    )
    assert r.status_code == 403
    assert "disabled" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_register_requires_secret_code_when_set(client, monkeypatch):
    """When ADMIN_REGISTRATION_CODE is set, code is required."""
    monkeypatch.setattr(settings, "ADMIN_REGISTRATION_CODE", "super-secret-code")

    # No code -> 403
    r = await client.post(
        "/api/v1/auth/register/admin",
        json=_payload("no-code@negotiator-ai.com"),
    )
    assert r.status_code == 403
    assert "code" in r.json()["detail"].lower()

    # Wrong code -> 403
    r = await client.post(
        "/api/v1/auth/register/admin",
        json=_payload("wrong-code@negotiator-ai.com", code="wrong"),
    )
    assert r.status_code == 403

    # Correct code -> 201
    r = await client.post(
        "/api/v1/auth/register/admin",
        json=_payload("good-code@negotiator-ai.com", code="super-secret-code"),
    )
    assert r.status_code == 201