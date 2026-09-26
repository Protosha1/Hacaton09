# tests/test_ownership.py
"""
Security tests: users cannot access each other's sessions or data (FR-19).
"""
import pytest


@pytest.mark.asyncio
async def test_user_cannot_read_other_session_analysis(
    client, seeded_db, user_1_token, user_token, auth_headers_factory,
    mock_llm, mock_analysis,
):
    """user-1 starts + ends a session; testuser cannot read its analysis."""
    h1 = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=h1,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]
    await client.post(
        "/api/v1/negotiation/message",
        headers=h1,
        json={"session_id": session_id, "message": "Hi"},
    )
    await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=h1,
    )

    h2 = auth_headers_factory(user_token)
    r = await client.get(
        f"/api/v1/negotiation/analysis/{session_id}",
        headers=h2,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_message_other_session(
    client, seeded_db, user_1_token, user_token, auth_headers_factory, mock_llm,
):
    h1 = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=h1,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]

    h2 = auth_headers_factory(user_token)
    r = await client.post(
        "/api/v1/negotiation/message",
        headers=h2,
        json={"session_id": session_id, "message": "Hijack"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_interrupt_other_session(
    client, seeded_db, user_1_token, user_token, auth_headers_factory, mock_llm,
):
    h1 = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=h1,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]

    h2 = auth_headers_factory(user_token)
    r = await client.post(
        f"/api/v1/negotiation/{session_id}/interrupt",
        headers=h2,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_end_other_session(
    client, seeded_db, user_1_token, user_token, auth_headers_factory, mock_llm,
):
    h1 = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/start",
        headers=h1,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]

    h2 = auth_headers_factory(user_token)
    r = await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=h2,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_list_other_user_sessions(
    client, seeded_db, user_1_token, user_token, auth_headers_factory,
):
    h2 = auth_headers_factory(user_token)
    r = await client.get(
        "/api/v1/negotiation/sessions/user-1",
        headers=h2,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_skills(
    client, seeded_db, user_1_token, user_token, auth_headers_factory,
):
    h2 = auth_headers_factory(user_token)
    r = await client.get(
        "/api/v1/users/user-1/skills",
        headers=h2,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_recommendations(
    client, seeded_db, user_1_token, user_token, auth_headers_factory,
):
    h2 = auth_headers_factory(user_token)
    r = await client.get(
        "/api/v1/users/user-1/recommendations",
        headers=h2,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_read_other_user_progress(
    client, seeded_db, user_1_token, user_token, auth_headers_factory,
):
    h2 = auth_headers_factory(user_token)
    r = await client.get(
        "/api/v1/negotiation/progress/user-1",
        headers=h2,
    )
    assert r.status_code == 403