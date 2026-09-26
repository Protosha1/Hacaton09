# tests/test_history.py
import pytest


@pytest.mark.asyncio
async def test_list_user_sessions_empty(client, seeded_db, user_1_token, auth_headers_factory):
    headers = auth_headers_factory(user_1_token)
    r = await client.get(
        "/api/v1/negotiation/sessions/user-1",
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_user_sessions(client, seeded_db, user_1_token, auth_headers_factory, mock_llm):
    headers = auth_headers_factory(user_1_token)
    await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    r = await client.get(
        "/api/v1/negotiation/sessions/user-1",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["scenario_name"] == "Tough Buyer"
    assert data[0]["status"] == "ongoing"


@pytest.mark.asyncio
async def test_get_session_messages(client, seeded_db, user_1_token, auth_headers_factory, mock_llm):
    headers = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]
    await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Test message"},
    )
    r = await client.get(
        f"/api/v1/negotiation/sessions/{session_id}/messages",
        headers=headers,
    )
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) >= 2
    assert msgs[0]["sender"] == "ai"
    assert msgs[1]["sender"] == "user"