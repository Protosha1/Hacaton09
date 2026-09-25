# tests/test_skills.py
"""
Tests for SkillProgress (FR-24).
"""
import pytest
from sqlalchemy import select

from app.models.skill_progress import SkillProgress
from app.core.skills import update_skills_for_user


@pytest.mark.asyncio
async def test_first_session_initializes_skill(seeded_db):
    scores = {
        "emotion_control_score": 80,
        "batna_score": 60,
        "spin_score": 40,
    }
    await update_skills_for_user(seeded_db, "user-1", scores)
    await seeded_db.commit()

    result = await seeded_db.execute(
        select(SkillProgress).where(SkillProgress.user_id == "user-1")
    )
    rows = {r.metric: r for r in result.scalars().all()}

    assert rows["emotion_control"].current_value == 80
    assert rows["batna"].current_value == 60
    assert rows["spin"].current_value == 40
    assert rows["emotion_control"].sessions_count == 1


@pytest.mark.asyncio
async def test_second_session_uses_ema_formula(seeded_db):
    await update_skills_for_user(
        seeded_db, "user-1",
        {"emotion_control_score": 100, "batna_score": 100, "spin_score": 100},
    )
    await seeded_db.commit()

    await update_skills_for_user(
        seeded_db, "user-1",
        {"emotion_control_score": 0, "batna_score": 0, "spin_score": 0},
    )
    await seeded_db.commit()

    result = await seeded_db.execute(
        select(SkillProgress)
        .where(SkillProgress.user_id == "user-1")
        .where(SkillProgress.metric == "emotion_control")
    )
    row = result.scalar_one()
    assert row.current_value == 70
    assert row.sessions_count == 2
    assert row.history == [100, 0]


@pytest.mark.asyncio
async def test_end_session_updates_skills(
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
        json={"session_id": session_id, "message": "Hello"},
    )

    r = await client.post(
        "/api/v1/negotiation/end?session_id=" + session_id,
        headers=headers,
    )
    assert r.status_code == 200

    r = await client.get(
        "/api/v1/users/user-1/skills",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == "user-1"

    metrics = {item["metric"]: item for item in data["skills"]}
    assert set(metrics.keys()) == {"emotion_control", "batna", "spin"}

    assert metrics["emotion_control"]["current_value"] == 85
    assert metrics["batna"]["current_value"] == 65
    assert metrics["spin"]["current_value"] == 70
    assert metrics["emotion_control"]["sessions_count"] == 1


@pytest.mark.asyncio
async def test_skills_empty_state(client, seeded_db, user_1_token, auth_headers_factory):
    headers = auth_headers_factory(user_1_token)

    r = await client.get("/api/v1/users/user-1/skills", headers=headers)
    assert r.status_code == 200
    data = r.json()

    metrics = {item["metric"]: item for item in data["skills"]}
    assert set(metrics.keys()) == {"emotion_control", "batna", "spin"}
    for m in metrics.values():
        assert m["current_value"] == 0
        assert m["sessions_count"] == 0


@pytest.mark.asyncio
async def test_skills_requires_token(client, seeded_db):
    r = await client.get("/api/v1/users/user-1/skills")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_skills_forbidden_for_admin(client, seeded_db):
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "skilladmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Skill Admin",
            "consent_given": True,
        },
    )
    token = reg.json()["access_token"]

    r = await client.get(
        "/api/v1/users/user-1/skills",
        headers={"Authorization": "Bearer " + token},
    )
    assert r.status_code == 403