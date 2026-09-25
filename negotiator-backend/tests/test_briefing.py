# tests/test_briefing.py
"""
Tests for briefing endpoint (FR-15).
"""
import pytest


@pytest.mark.asyncio
async def test_briefing_returns_public_data(
    client, seeded_db, user_1_token, auth_headers_factory
):
    headers = auth_headers_factory(user_1_token)
    r = await client.get(
        "/api/v1/negotiation/briefing/scenario-1",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()

    assert data["scenario_id"] == "scenario-1"
    assert data["name"] == "Tough Buyer"
    assert data["user_role"] == "Seller"
    assert data["user_goal"] == "Sell at $1000+"
    assert data["opponent_role"] == "Buyer"
    assert data["initial_message"] == "Hello. What is your price?"


@pytest.mark.asyncio
async def test_briefing_hides_spoilers(
    client, seeded_db, user_1_token, auth_headers_factory
):
    headers = auth_headers_factory(user_1_token)
    r = await client.get(
        "/api/v1/negotiation/briefing/scenario-1",
        headers=headers,
    )
    data = r.json()

    assert "opponent_character" not in data
    assert "opponent_goal" not in data
    assert "opponent_interests" not in data
    assert "opponent_constraints" not in data
    assert "opponent_red_lines" not in data
    assert "tactics" not in data
    assert "concession_limits" not in data


@pytest.mark.asyncio
async def test_briefing_unknown_scenario(
    client, seeded_db, user_1_token, auth_headers_factory
):
    headers = auth_headers_factory(user_1_token)
    r = await client.get(
        "/api/v1/negotiation/briefing/ghost",
        headers=headers,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_briefing_requires_token(client, seeded_db):
    r = await client.get("/api/v1/negotiation/briefing/scenario-1")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_briefing_forbidden_for_admin(client, seeded_db):
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "briefadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Brief Admin",
            "consent_given": True,
        },
    )
    token = reg.json()["access_token"]

    r = await client.get(
        "/api/v1/negotiation/briefing/scenario-1",
        headers={"Authorization": "Bearer " + token},
    )
    assert r.status_code == 403