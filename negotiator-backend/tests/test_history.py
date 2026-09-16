# tests/test_history.py
import pytest


@pytest.mark.asyncio
async def test_list_user_sessions_empty(client):
    r = await client.get("/api/v1/negotiation/sessions/user-1")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_user_sessions(client, seeded_db, mock_llm):
    await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    r = await client.get("/api/v1/negotiation/sessions/user-1")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["scenario_name"] == "Tough Buyer"
    assert data[0]["status"] == "ongoing"


@pytest.mark.asyncio
async def test_get_session_messages(client, seeded_db, mock_llm):
    r = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]
    await client.post(
        "/api/v1/negotiation/message",
        json={"session_id": session_id, "message": "Test message"},
    )
    r = await client.get(f"/api/v1/negotiation/sessions/{session_id}/messages")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) >= 2
    assert msgs[0]["sender"] == "ai"
    assert msgs[1]["sender"] == "user"