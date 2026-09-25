# tests/test_interrupted.py
"""
Tests for interrupted sessions (FR-21).
"""
import pytest


# =========================
# POST /negotiation/{id}/interrupt
# =========================

@pytest.mark.asyncio
async def test_interrupt_session_success(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm
):
    headers = auth_headers_factory(user_1_token)

    # Start a session
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    # Interrupt it
    r = await client.post(
        f"/api/v1/negotiation/{session_id}/interrupt",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "interrupted"
    assert data["finished_at"] is not None


@pytest.mark.asyncio
async def test_interrupt_idempotent(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm
):
    """Calling interrupt twice returns the same state."""
    headers = auth_headers_factory(user_1_token)

    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    r1 = await client.post(
        f"/api/v1/negotiation/{session_id}/interrupt", headers=headers,
    )
    r2 = await client.post(
        f"/api/v1/negotiation/{session_id}/interrupt", headers=headers,
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["finished_at"] == r2.json()["finished_at"]


@pytest.mark.asyncio
async def test_cannot_interrupt_finished_session(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis
):
    headers = auth_headers_factory(user_1_token)

    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Hello"},
    )
    await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=headers,
    )

    r = await client.post(
        f"/api/v1/negotiation/{session_id}/interrupt",
        headers=headers,
    )
    assert r.status_code == 400
    assert "finished" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_interrupt_unknown_session(client, seeded_db, user_1_token, auth_headers_factory):
    headers = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/ghost-session/interrupt",
        headers=headers,
    )
    assert r.status_code == 404


# =========================
# POST /negotiation/message to interrupted session
# =========================

@pytest.mark.asyncio
async def test_cannot_message_interrupted_session(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm
):
    headers = auth_headers_factory(user_1_token)

    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    await client.post(
        f"/api/v1/negotiation/{session_id}/interrupt",
        headers=headers,
    )

    r = await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Still here?"},
    )
    assert r.status_code == 400
    assert "interrupted" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cannot_end_interrupted_session(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm
):
    headers = auth_headers_factory(user_1_token)

    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    await client.post(
        f"/api/v1/negotiation/{session_id}/interrupt",
        headers=headers,
    )

    r = await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=headers,
    )
    assert r.status_code == 400
    assert "interrupted" in r.json()["detail"].lower()


# =========================
# GET /users/{id}/interrupted-session
# =========================

@pytest.mark.asyncio
async def test_interrupted_session_empty(
    client, seeded_db, user_1_token, auth_headers_factory
):
    headers = auth_headers_factory(user_1_token)

    r = await client.get(
        "/api/v1/users/user-1/interrupted-session",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["has_interrupted"] is False
    assert data["session"] is None


@pytest.mark.asyncio
async def test_interrupted_session_returns_last(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm
):
    headers = auth_headers_factory(user_1_token)

    # Create two sessions, interrupt both
    r1 = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    s1 = r1.json()["session_id"]

    r2 = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    s2 = r2.json()["session_id"]

    await client.post(f"/api/v1/negotiation/{s1}/interrupt", headers=headers)
    await client.post(f"/api/v1/negotiation/{s2}/interrupt", headers=headers)

    r = await client.get(
        "/api/v1/users/user-1/interrupted-session",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["has_interrupted"] is True
    # Most recent = s2
    assert data["session"]["session_id"] == s2
    assert data["session"]["scenario_name"] == "Tough Buyer"


@pytest.mark.asyncio
async def test_interrupted_session_requires_token(client, seeded_db):
    r = await client.get("/api/v1/users/user-1/interrupted-session")
    assert r.status_code == 401