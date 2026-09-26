# tests/test_services_unit.py
"""
Unit tests for services - no HTTP, no LLM, no Whisper.
"""
import pytest

from app.services.negotiation_service import NegotiationService
from app.services.voice_service import VoiceService
from app.core.xp import calculate_xp, get_rank, is_perfect_run
from app.core.skills import METRICS, HISTORY_WEIGHT, SESSION_WEIGHT


# =========================
# NegotiationService._build_system_prompt
# =========================

def _make_scenario():
    class S:
        opponent_role = "Buyer"
        opponent_character = "Tough, skeptical"
        opponent_goal = "Buy at $900"
        opponent_interests = ["fast delivery"]
        opponent_constraints = ["needs approval"]
        opponent_red_lines = ["rudeness"]
        concession_limits = {"price_min": 900, "max_concessions": 3}
        tactics = ["anchor_low"]
        communication_style = "Business-like"
        tone_behavior = None
        non_standard_case = None
    return S()


def test_build_prompt_contains_difficulty_beginner():
    prompt = NegotiationService._build_system_prompt(
        _make_scenario(), difficulty="beginner",
        relationship="stranger", power_balance="equal",
    )
    assert "BEGINNER" in prompt
    assert "Buyer" in prompt
    assert "$900" in prompt or "900" in prompt


def test_build_prompt_contains_difficulty_expert():
    prompt = NegotiationService._build_system_prompt(
        _make_scenario(), difficulty="expert",
        relationship="stranger", power_balance="equal",
    )
    assert "EXPERT" in prompt


def test_build_prompt_contains_relationship():
    prompt = NegotiationService._build_system_prompt(
        _make_scenario(), difficulty="practitioner",
        relationship="subordinate", power_balance="equal",
    )
    assert "boss" in prompt.lower() or "subordinate" in prompt.lower()


def test_build_prompt_contains_power_balance():
    prompt = NegotiationService._build_system_prompt(
        _make_scenario(), difficulty="practitioner",
        relationship="stranger", power_balance="opponent_strong",
    )
    assert "leverage" in prompt.lower() or "power" in prompt.lower()


def test_build_prompt_handles_none_scenario():
    prompt = NegotiationService._build_system_prompt(
        None, difficulty="practitioner",
        relationship="stranger", power_balance="equal",
    )
    assert "counterparty" in prompt.lower()


# =========================
# VoiceService.speech_to_text (with mocked WhisperModel)
# =========================

@pytest.fixture
def mock_whisper(monkeypatch):
    """Replace WhisperModel with a fake that returns canned segments."""
    from app.services import voice_service

    class FakeSegment:
        def __init__(self, text):
            self.text = text

    class FakeModel:
        def transcribe(self, path, language=None, beam_size=None, vad_filter=None):
            # Return iterable of segments + info
            return iter([FakeSegment("Hello"), FakeSegment("world")]), None

    def fake_get_model(cls):
        return FakeModel()

    monkeypatch.setattr(
        voice_service.VoiceService, "_get_model", classmethod(fake_get_model)
    )


@pytest.mark.asyncio
async def test_speech_to_text_returns_joined_text(mock_whisper):
    result = await VoiceService.speech_to_text(b"FAKE_AUDIO")
    assert result == "Hello world"


# =========================
# XP sanity (already covered, but keep here for completeness)
# =========================

def test_xp_and_rank_are_consistent():
    xp = calculate_xp("expert", "yes", perfect=True)
    rank = get_rank(xp)
    assert xp == 250
    assert rank["level"] >= 1


# =========================
# Skill constants
# =========================

def test_skill_constants():
    assert set(METRICS) == {"emotion_control", "batna", "spin"}
    assert HISTORY_WEIGHT + SESSION_WEIGHT == pytest.approx(1.0)