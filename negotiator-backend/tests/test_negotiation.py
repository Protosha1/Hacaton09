# tests/test_negotiation.py
import pytest


@pytest.mark.asyncio
async def test_start_session(client, seeded_db):
    response = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["role"] == "Seller"
    assert data["opponent"] == "Buyer"
    assert data["first_message"] == "Hello. What is your price?"


@pytest.mark.asyncio
async def test_start_session_unknown_scenario(client):
    response = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "ghost", "user_id": "user-1"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_send_message(client, seeded_db, mock_llm):
    # Start
    r = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    # Send
    r = await client.post(
        "/api/v1/negotiation/message",
        json={"session_id": session_id, "message": "Our price is $1200."},
    )
    assert r.status_code == 200
    data = r.json()
    assert "[MOCKED LLM]" in data["reply"]
    assert data["session_status"] == "ongoing"


@pytest.mark.asyncio
async def test_send_message_unknown_session(client, mock_llm):
    r = await client.post(
        "/api/v1/negotiation/message",
        json={"session_id": "ghost", "message": "hi"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_end_session(client, seeded_db, mock_llm, mock_analysis):
    # Start
    r = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    # Send at least one message
    await client.post(
        "/api/v1/negotiation/message",
        json={"session_id": session_id, "message": "Hello"},
    )

    # End
    r = await client.post(f"/api/v1/negotiation/end?session_id={session_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["overall_score"] == 78
    assert data["goal_achieved"] == "yes"


@pytest.mark.asyncio
async def test_get_analysis_after_end(client, seeded_db, mock_llm, mock_analysis):
    r = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]
    await client.post(
        "/api/v1/negotiation/message",
        json={"session_id": session_id, "message": "Hello"},
    )
    await client.post(f"/api/v1/negotiation/end?session_id={session_id}")

    r = await client.get(f"/api/v1/negotiation/analysis/{session_id}")
    assert r.status_code == 200
    assert r.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_send_message_to_finished_session(client, seeded_db, mock_llm, mock_analysis):
    """After /end, /message should return 400."""
    # Start
    r = await client.post(
        "/api/v1/negotiation/start",
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    # Send one message and finish
    await client.post(
        "/api/v1/negotiation/message",
        json={"session_id": session_id, "message": "Hello"},
    )
    await client.post(f"/api/v1/negotiation/end?session_id={session_id}")

    # Try to send another message -> should fail with 400
    r = await client.post(
        "/api/v1/negotiation/message",
        json={"session_id": session_id, "message": "One more thing"},
    )
    assert r.status_code == 400