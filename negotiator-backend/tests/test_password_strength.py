# tests/test_password_strength.py
"""
Tests for password strength validation (FR-11).
Rules: min 8 chars + 1 uppercase + 1 lowercase + 1 digit.
"""
import pytest


@pytest.mark.asyncio
async def test_password_without_uppercase_rejected(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "noupper@example.com",
            "password": "secret1234",
            "name": "No Upper",
            "consent_given": True,
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_password_without_lowercase_rejected(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nolower@example.com",
            "password": "SECRET1234",
            "name": "No Lower",
            "consent_given": True,
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_password_without_digit_rejected(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nodigit@example.com",
            "password": "SecretPass",
            "name": "No Digit",
            "consent_given": True,
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_password_without_letters_rejected(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "digitsonly@example.com",
            "password": "12345678",
            "name": "Digits",
            "consent_given": True,
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_strong_password_accepted(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "strong@example.com",
            "password": "Secret1234",
            "name": "Strong",
            "consent_given": True,
        },
    )
    assert r.status_code == 201
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_strong_password_with_special_chars_accepted(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "strongspecial@example.com",
            "password": "MyPassw0rd",
            "name": "Strong Special",
            "consent_given": True,
        },
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_exactly_eight_chars_with_all_classes_accepted(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "eight@example.com",
            "password": "Abcdefg1",
            "name": "Eight",
            "consent_given": True,
        },
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_admin_weak_password_rejected(client):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "weakadmin@negotiator-ai.com",
            "password": "weakpass",
            "name": "Weak Admin",
            "consent_given": True,
        },
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_admin_strong_password_accepted(client):
    r = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "strongadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Strong Admin",
            "consent_given": True,
        },
    )
    assert r.status_code == 201