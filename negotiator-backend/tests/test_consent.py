# tests/test_consent.py
"""
Tests for consent_given (v8 privacy).
consent_given is now REQUIRED - no default value.
"""
import pytest


@pytest.mark.asyncio
async def test_register_without_consent_rejected(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "noconsent@example.com",
            "password": "Secret1234",
            "name": "No Consent",
            "consent_given": False,
        },
    )
    assert r.status_code == 400
    assert "consent" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_with_consent_success(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "consent@example.com",
            "password": "Secret1234",
            "name": "Consent",
            "consent_given": True,
        },
    )
    assert r.status_code == 201
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_register_without_consent_field_rejected(client):
    """Missing consent_given -> 422 (schema requires it)."""
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "omitted@example.com",
            "password": "Secret1234",
            "name": "Omitted",
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_me_shows_consent_given(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "showconsent@example.com",
            "password": "Secret1234",
            "name": "Show",
            "consent_given": True,
        },
    )
    token = reg.json()["access_token"]

    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer " + token},
    )
    assert r.status_code == 200
    assert r.json()["consent_given"] is True


@pytest.mark.asyncio
async def test_admin_register_without_consent_rejected(client):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "noconsentadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Admin No Consent",
            "consent_given": False,
        },
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_admin_register_without_consent_field_rejected(client):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "omittedadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Admin Omitted",
        },
    )
    assert r.status_code == 422