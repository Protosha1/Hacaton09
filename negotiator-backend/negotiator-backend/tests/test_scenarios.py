# tests/test_scenarios.py
import pytest


@pytest.mark.asyncio
async def test_list_scenarios_empty(client):
    """Empty DB → empty list."""
    response = await client.get("/api/v1/scenarios/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_scenarios_with_data(client, seeded_db):
    """After seed → one scenario in the list."""
    response = await client.get("/api/v1/scenarios/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "scenario-1"
    assert data[0]["name"] == "Tough Buyer"


@pytest.mark.asyncio
async def test_get_scenario_detail(client, seeded_db):
    """Details include spoiler fields."""
    response = await client.get("/api/v1/scenarios/scenario-1")
    assert response.status_code == 200
    data = response.json()
    assert data["opponent_goal"] == "Buy at $900"
    assert data["concession_limits"]["price_min"] == 900
    assert data["initial_message"] == "Hello. What is your price?"


@pytest.mark.asyncio
async def test_get_scenario_not_found(client):
    """Unknown ID → 404."""
    response = await client.get("/api/v1/scenarios/nonexistent")
    assert response.status_code == 404