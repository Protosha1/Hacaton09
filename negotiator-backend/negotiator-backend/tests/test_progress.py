# tests/test_progress.py
"""
Tests for GET /negotiation/progress/{user_id}.
"""
import pytest


@pytest.mark.asyncio
async def test_progress_empty(client, seeded_db, user_1_token, auth_headers_factory):
    """No finished sessions -> all zeros."""
    headers = auth_headers_factory(user_1_token)
    r = await client.get("/api/v1/negotiation/progress/user-1", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_sessions"] == 0
    assert data["finished_sessions"] == 0
    assert data["average_overall"] == 0.0
    assert data["goal_achieved_count"] == 0


@pytest.mark.asyncio
async def test_progress_after_one_session(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis
):
    """After 1 finished session -> averages match that session."""
    headers = auth_headers_factory(user_1_token)

    # Start + message + end
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    await client.post(
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Hi"},
    )
    await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=headers,
    )

    # Check progress
    r = await client.get("/api/v1/negotiation/progress/user-1", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_sessions"] == 1
    assert data["finished_sessions"] == 1
    # mock_analysis returns: overall=78, argumentation=80, objection=75, spin=70, batna=65, emotion=85
    assert data["average_overall"] == 78.0
    assert data["average_argumentation"] == 80.0
    assert data["average_objection_handling"] == 75.0
    assert data["average_spin"] == 70.0
    assert data["average_batna"] == 65.0
    assert data["average_emotion_control"] == 85.0
    assert data["goal_achieved_count"] == 1


@pytest.mark.asyncio
async def test_progress_two_sessions(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis
):
    """After 2 sessions -> averages are (a+b)/2."""
    headers = auth_headers_factory(user_1_token)

    for _ in range(2):
        r = await client.post(
            "/api/v1/negotiation/start",
            headers=headers,
            json={"scenario_id": "scenario-1", "user_id": "user-1"},
        )
        sid = r.json()["session_id"]
        await client.post(
            "/api/v1/negotiation/message",
            headers=headers,
            json={"session_id": sid, "message": "Hi"},
        )
        await client.post(
            f"/api/v1/negotiation/end?session_id={sid}",
            headers=headers,
        )

    r = await client.get("/api/v1/negotiation/progress/user-1", headers=headers)
    data = r.json()
    assert data["total_sessions"] == 2
    assert data["average_overall"] == 78.0   # (78+78)/2


@pytest.mark.asyncio
async def test_progress_requires_token(client, seeded_db):
    r = await client.get("/api/v1/negotiation/progress/user-1")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_progress_forbidden_for_admin(client, seeded_db):
    """Admin -> 403 (FR-19)."""
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "progadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Prog Admin",
        },
    )
    token = reg.json()["access_token"]

    r = await client.get(
        "/api/v1/negotiation/progress/user-1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403