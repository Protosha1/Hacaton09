# tests/test_avatar_and_prompt.py
"""
Tests for:
- avatar_url in user profile (FR-20)
- tone_behavior and non_standard_case in system prompt (FR-33, FR-46)
"""
import pytest

from app.services.negotiation_service import NegotiationService
from app.core.constants import Difficulty


def _make_scenario_with_admin_fields():
    class S:
        opponent_role = "Buyer"
        opponent_character = "Tough"
        opponent_goal = "Buy at $900"
        opponent_interests = ["fast delivery"]
        opponent_constraints = ["needs approval"]
        opponent_red_lines = ["rudeness"]
        concession_limits = {"price_min": 900, "max_concessions": 3}
        tactics = ["anchor_low"]
        communication_style = "Business-like"
        tone_behavior = "Cold and analytical, no small talk"
        non_standard_case = "Mid-conversation you reveal a competitor's lower offer"
    return S()


# =========================
# Avatar (FR-20)
# =========================

@pytest.mark.asyncio
async def test_me_returns_avatar_url_field(client, seeded_db, user_1_token, auth_headers_factory):
    """GET /me must include avatar_url (even if null)."""
    headers = auth_headers_factory(user_1_token)
    r = await client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "avatar_url" in data
    assert data["avatar_url"] is None  # not set yet


@pytest.mark.asyncio
async def test_register_returns_avatar_url_field(client):
    """New user /me has avatar_url=None."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "avatartest@example.com",
            "password": "Secret1234",
            "name": "Avatar Test",
        },
    )
    token = reg.json()["access_token"]
    r = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["avatar_url"] is None


# =========================
# Prompt: tone_behavior (FR-46)
# =========================

def test_prompt_includes_tone_behavior():
    prompt = NegotiationService._build_system_prompt(
        _make_scenario_with_admin_fields(),
        difficulty=Difficulty.PRACTITIONER,
        relationship="stranger",
        power_balance="equal",
    )
    assert "Cold and analytical" in prompt


def test_prompt_without_tone_behavior_has_no_empty_block():
    """If tone_behavior is None, the tone block is skipped."""
    class S:
        opponent_role = "Buyer"
        opponent_character = "Tough"
        opponent_goal = "Buy at $900"
        opponent_interests = []
        opponent_constraints = []
        opponent_red_lines = []
        concession_limits = {}
        tactics = []
        communication_style = "Business-like"
        tone_behavior = None
        non_standard_case = None
    prompt = NegotiationService._build_system_prompt(
        S(), difficulty="practitioner", relationship="stranger", power_balance="equal",
    )
    assert "TONE / BEHAVIOR" not in prompt


# =========================
# Prompt: non_standard_case (FR-33)
# =========================

def test_prompt_excludes_twist_on_beginner():
    """On beginner difficulty the twist MUST NOT be included (FR-33)."""
    prompt = NegotiationService._build_system_prompt(
        _make_scenario_with_admin_fields(),
        difficulty=Difficulty.BEGINNER,
        relationship="stranger",
        power_balance="equal",
    )
    assert "NON-STANDARD CASE" not in prompt
    assert "competitor" not in prompt


def test_prompt_includes_twist_on_practitioner():
    prompt = NegotiationService._build_system_prompt(
        _make_scenario_with_admin_fields(),
        difficulty=Difficulty.PRACTITIONER,
        relationship="stranger",
        power_balance="equal",
    )
    assert "NON-STANDARD CASE" in prompt
    assert "competitor" in prompt


def test_prompt_includes_twist_on_expert():
    prompt = NegotiationService._build_system_prompt(
        _make_scenario_with_admin_fields(),
        difficulty=Difficulty.EXPERT,
        relationship="stranger",
        power_balance="equal",
    )
    assert "NON-STANDARD CASE" in prompt


def test_prompt_without_twist_has_no_block():
    """If scenario has no twist, block is skipped."""
    class S:
        opponent_role = "Buyer"
        opponent_character = "Tough"
        opponent_goal = "Buy at $900"
        opponent_interests = []
        opponent_constraints = []
        opponent_red_lines = []
        concession_limits = {}
        tactics = []
        communication_style = "Business-like"
        tone_behavior = None
        non_standard_case = None
    prompt = NegotiationService._build_system_prompt(
        S(), difficulty="expert", relationship="stranger", power_balance="equal",
    )
    assert "NON-STANDARD CASE" not in prompt