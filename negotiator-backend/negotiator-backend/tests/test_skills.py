# tests/test_skills.py
"""
Tests for SkillProgress (FR-24).
"""
import pytest
from sqlalchemy import select

from app.models.skill_progress import SkillProgress
from app.core.skills import update_skills_for_user


# =========================
# Pure function tests
# =========================

@pytest.mark.asyncio
async def test_first_session_initializes_skill(seeded_db):
    """First session for a metric -> current_value = session_score."""
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
    """new_value = old * 0.7 + new_score * 0.3"""
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


# =========================
# Integration: /end updates skills
# =========================

@pytest.mark.asyncio
async def test_end_session_updates_skills(
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

    r = await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
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
    """User with no sessions -> all 3 metrics present with 0."""
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
    """No token -> 401."""
    r = await client.get("/api/v1/users/user-1/skills")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_skills_forbidden_for_admin(client, seeded_db):
    """Admin -> 403 (FR-19)."""
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "skilladmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Skill Admin",
        },
    )
    token = reg.json()["access_token"]

    r = await client.get(
        "/api/v1/users/user-1/skills",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403