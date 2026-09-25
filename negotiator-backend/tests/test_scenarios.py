# tests/test_scenarios.py
import pytest


@pytest.mark.asyncio
async def test_list_scenarios_empty(client):
    """Empty DB -> empty list."""
    response = await client.get("/api/v1/scenarios/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_scenarios_with_data(client, seeded_db):
    """After seed -> one scenario in the list."""
    response = await client.get("/api/v1/scenarios/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "scenario-1"
    assert data[0]["name"] == "Tough Buyer"


@pytest.mark.asyncio
async def test_get_scenario_returns_no_spoilers(client, seeded_db):
    """Public preview does NOT expose opponent_goal, tactics, concession_limits."""
    response = await client.get("/api/v1/scenarios/scenario-1")
    assert response.status_code == 200
    data = response.json()

    # Public fields present
    assert data["id"] == "scenario-1"
    assert data["name"] == "Tough Buyer"
    assert data["category"] == "clients"
    assert data["user_role"] == "Seller"
    assert data["opponent_role"] == "Buyer"

    # Spoilers absent
    assert "opponent_goal" not in data
    assert "opponent_character" not in data
    assert "opponent_interests" not in data
    assert "opponent_red_lines" not in data
    assert "concession_limits" not in data
    assert "tactics" not in data
    assert "initial_message" not in data


@pytest.mark.asyncio
async def test_get_scenario_not_found(client):
    """Unknown ID -> 404."""
    response = await client.get("/api/v1/scenarios/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_scenario_admin_draft_hidden(client):
    """Drafts from admins are not visible publicly."""
    at = (await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "hidden-scen@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Hidden Admin",
            "consent_given": True,
        },
    )).json()["access_token"]

    await client.post(
        "/api/v1/scenarios/",
        headers={"Authorization": f"Bearer {at}"},
        json={
            "id": "secret-draft",
            "name": "Secret",
            "opponent_goal": "Never share this",
        },
    )

    r = await client.get("/api/v1/scenarios/secret-draft")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_scenario_admin_view_returns_spoilers(client):
    """Admin sees all fields through /scenarios/{id}/admin."""
    at = (await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "viewer-scen@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Viewer Admin",
            "consent_given": True,
        },
    )).json()["access_token"]

    await client.post(
        "/api/v1/scenarios/",
        headers={"Authorization": f"Bearer {at}"},
        json={
            "id": "admin-view",
            "name": "Admin View",
            "opponent_goal": "Secret goal",
            "concession_limits": {"price_min": 100},
        },
    )

    r = await client.get(
        "/api/v1/scenarios/admin-view/admin",
        headers={"Authorization": f"Bearer {at}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["opponent_goal"] == "Secret goal"
    assert data["concession_limits"]["price_min"] == 100