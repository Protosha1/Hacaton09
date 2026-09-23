# tests/test_consent.py
"""
Tests for consent_given (v8 privacy).
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
async def test_register_without_consent_field_defaults_true(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "omitted@example.com",
            "password": "Secret1234",
            "name": "Omitted",
        },
    )
    assert r.status_code == 201


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
        headers={"Authorization": f"Bearer {token}"},
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
    assert "consent" in r.json()["detail"].lower()