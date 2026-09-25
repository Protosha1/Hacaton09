# tests/test_xp.py
"""
Tests for XP calculation and rank system (FR-39, FR-40, FR-41).
"""
import pytest
from sqlalchemy import select

from app.core.xp import (
    calculate_xp,
    get_rank,
    is_perfect_run,
    BASE_XP,
    VERDICT_MULTIPLIER,
    PERFECT_BONUS_XP,
)
from app.models.user import User


# =========================
# Pure functions
# =========================

def test_get_rank_thresholds():
    """Rank thresholds per FR-39."""
    assert get_rank(0)["level"] == 1
    assert get_rank(50)["level"] == 1
    assert get_rank(99)["level"] == 1
    assert get_rank(100)["level"] == 2
    assert get_rank(399)["level"] == 2
    assert get_rank(400)["level"] == 3
    assert get_rank(699)["level"] == 3
    assert get_rank(700)["level"] == 4
    assert get_rank(5000)["level"] == 4


def test_get_rank_names():
    assert get_rank(0)["name"] == "Ученик школы диалога"
    assert get_rank(200)["name"] == "Мастер тактики"
    assert get_rank(500)["name"] == "Хищник аргументов"
    assert get_rank(1000)["name"] == "Властелин аргументов"


def test_calculate_xp_table():
    """Verify the FR-40 table."""
    assert calculate_xp("beginner", "no") == 10
    assert calculate_xp("beginner", "partial") == 30
    assert calculate_xp("beginner", "yes") == 50

    assert calculate_xp("practitioner", "no") == 20
    assert calculate_xp("practitioner", "partial") == 60
    assert calculate_xp("practitioner", "yes") == 100

    assert calculate_xp("expert", "no") == 40
    assert calculate_xp("expert", "partial") == 120
    assert calculate_xp("expert", "yes") == 200


def test_calculate_xp_perfect_bonus():
    """+50 XP on expert/success/perfect (FR-41)."""
    assert calculate_xp("expert", "yes", perfect=True) == 250
    assert calculate_xp("practitioner", "yes", perfect=True) == 100
    assert calculate_xp("expert", "partial", perfect=True) == 120
    assert calculate_xp("expert", "yes", perfect=False) == 200


def test_is_perfect_run():
    perfect = {
        "argumentation_score": 85,
        "objection_handling_score": 80,
        "spin_score": 90,
        "batna_score": 85,
        "emotion_control_score": 95,
    }
    assert is_perfect_run(perfect) is True

    not_perfect = {**perfect, "batna_score": 79}
    assert is_perfect_run(not_perfect) is False

    empty = {}
    assert is_perfect_run(empty) is False


# =========================
# Integration: /end awards XP
# =========================

@pytest.mark.asyncio
async def test_end_session_awards_xp(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis
):
    """After /end, xp_earned field is 50 (beginner + success)."""
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
    data = r.json()
    assert data["xp_earned"] == 50
    assert data["is_perfect"] is False


@pytest.mark.asyncio
async def test_me_shows_updated_xp_and_rank(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis
):
    """After /end for user-1, /me (same token) shows total_xp=50 and rank=1."""
    headers = auth_headers_factory(user_1_token)

    # Start + send + end for user-1
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

    # The same token belongs to user-1 — /me returns user-1's profile
    r = await client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_xp"] == 50
    assert data["rank_level"] == 1
    assert data["rank_name"] == "Ученик школы диалога"