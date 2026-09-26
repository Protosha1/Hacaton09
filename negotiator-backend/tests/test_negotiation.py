# tests/test_negotiation.py
import pytest


@pytest.mark.asyncio
async def test_start_session(client, seeded_db, user_token, auth_headers_factory):
    headers = auth_headers_factory(user_token)
    response = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["role"] == "Seller"
    assert data["opponent"] == "Buyer"
    assert data["first_message"] == "Hello. What is your price?"


@pytest.mark.asyncio
async def test_start_session_unknown_scenario(client, user_token, auth_headers_factory):
    headers = auth_headers_factory(user_token)
    response = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "ghost"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message(client, seeded_db, user_token, auth_headers_factory, mock_llm):
    headers = auth_headers_factory(user_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]

    r = await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Our price is $1200."},
    )
    assert r.status_code == 200
    data = r.json()
    assert "[MOCKED LLM]" in data["reply"]
    assert data["session_status"] == "ongoing"


@pytest.mark.asyncio
async def test_send_message_unknown_session(client, user_token, auth_headers_factory, mock_llm):
    headers = auth_headers_factory(user_token)
    r = await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": "ghost", "message": "hi"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_end_session(client, seeded_db, user_token, auth_headers_factory, mock_llm, mock_analysis):
    headers = auth_headers_factory(user_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]

    await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Hello"},
    )

    r = await client.post(
        "/api/v1/negotiation/end?session_id=" + session_id,
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["overall_score"] == 78
    assert data["goal_achieved"] == "yes"


@pytest.mark.asyncio
async def test_get_analysis_after_end(client, seeded_db, user_token, auth_headers_factory, mock_llm, mock_analysis):
    headers = auth_headers_factory(user_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]
    await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Hello"},
    )
    await client.post(
        "/api/v1/negotiation/end?session_id=" + session_id,
        headers=headers,
    )

    r = await client.get(
        "/api/v1/negotiation/analysis/" + session_id,
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_send_message_to_finished_session(client, seeded_db, user_token, auth_headers_factory, mock_llm, mock_analysis):
    headers = auth_headers_factory(user_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]

    await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Hello"},
    )
    await client.post(
        "/api/v1/negotiation/end?session_id=" + session_id,
        headers=headers,
    )

    r = await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "One more thing"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_negotiation_start_forbidden_for_admin(client, seeded_db):
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "admin4start@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Admin 4 Start",
            "consent_given": True,
        },
    )
    token = reg.json()["access_token"]

    response = await client.post(
        "/api/v1/negotiation/start",
        headers={"Authorization": "Bearer " + token},
        json={"scenario_id": "scenario-1"},
    )
    assert response.status_code == 403
    assert "administrator" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_negotiation_start_without_token(client, seeded_db):
    response = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1"},
    )
    assert response.status_code == 401