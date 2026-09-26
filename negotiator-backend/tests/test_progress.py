# tests/test_progress.py
"""
Tests for GET /negotiation/progress/{user_id}.
"""
import pytest


@pytest.mark.asyncio
async def test_progress_empty(client, seeded_db, user_1_token, auth_headers_factory):
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
        json={"session_id": session_id, "message": "Hi"},
    )
    await client.post(
        "/api/v1/negotiation/end?session_id=" + session_id,
        headers=headers,
    )

    r = await client.get("/api/v1/negotiation/progress/user-1", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_sessions"] == 1
    assert data["finished_sessions"] == 1
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
    headers = auth_headers_factory(user_1_token)

    for _ in range(2):
        r = await client.post(
            "/api/v1/negotiation/start",
            headers=headers,
            json={"scenario_id": "scenario-1"},
        )
        sid = r.json()["session_id"]
        await client.post(
            "/api/v1/negotiation/message",
            headers=headers,
            json={"session_id": sid, "message": "Hi"},
        )
        await client.post(
            "/api/v1/negotiation/end?session_id=" + sid,
            headers=headers,
        )

    r = await client.get("/api/v1/negotiation/progress/user-1", headers=headers)
    data = r.json()
    assert data["total_sessions"] == 2
    assert data["average_overall"] == 78.0


@pytest.mark.asyncio
async def test_progress_requires_token(client, seeded_db):
    r = await client.get("/api/v1/negotiation/progress/user-1")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_progress_forbidden_for_admin(client, seeded_db):
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "progadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Prog Admin",
            "consent_given": True,
        },
    )
    token = reg.json()["access_token"]

    r = await client.get(
        "/api/v1/negotiation/progress/user-1",
        headers={"Authorization": "Bearer " + token},
    )
    assert r.status_code == 403