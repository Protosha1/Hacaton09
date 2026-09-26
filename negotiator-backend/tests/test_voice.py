# tests/test_voice.py
"""
Tests for POST /negotiation/voice (STT via Whisper -> LLM).
Whisper is mocked so tests run without loading the model.
"""
import pytest


@pytest.fixture
def mock_voice(monkeypatch):
    """Replace VoiceService.speech_to_text with a canned transcript."""
    from app.services import voice_service

    async def fake_stt(audio_bytes: bytes, language: str = "ru") -> str:
        return "Hello, I want to discuss a raise."

    monkeypatch.setattr(
        voice_service.VoiceService, "speech_to_text", fake_stt
    )


# =========================
# Happy path
# =========================

@pytest.mark.asyncio
async def test_voice_message_success(
    client, seeded_db, user_1_token, auth_headers_factory,
    mock_llm, mock_voice,
):
    headers = auth_headers_factory(user_1_token)

    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1"},
    )
    session_id = r.json()["session_id"]

    r = await client.post(
        "/api/v1/negotiation/voice",
        headers=headers,
        data={"session_id": session_id},
        files={"audio": ("voice.webm", b"FAKE_AUDIO_BYTES", "audio/webm")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["user_text"] == "Hello, I want to discuss a raise."
    assert "[MOCKED LLM]" in data["reply"]  # renamed from reply_text
    assert data["session_status"] == "ongoing"


# =========================
# Errors
# =========================

@pytest.mark.asyncio
async def test_voice_unknown_session(
    client, seeded_db, user_1_token, auth_headers_factory,
    mock_llm, mock_voice,
):
    """Unknown session_id -> 404."""
    headers = auth_headers_factory(user_1_token)
    r = await client.post(
        "/api/v1/negotiation/voice",
        headers=headers,
        data={"session_id": "ghost-session"},
        files={"audio": ("voice.webm", b"FAKE", "audio/webm")},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_voice_requires_token(client, seeded_db):
    """No auth -> 401."""
    r = await client.post(
        "/api/v1/negotiation/voice",
        data={"session_id": "any"},
        files={"audio": ("voice.webm", b"FAKE", "audio/webm")},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_voice_forbidden_for_admin(client, seeded_db):
    """Admin -> 403 (FR-19)."""
    reg = await client.post(
        "/api/v1/auth/register/admin",
        json={
            "email": "voiceadmin@negotiator-ai.com",
            "password": "AdminPass123",
            "name": "Voice Admin",
            "consent_given": True,
        },
    )
    token = reg.json()["access_token"]

    r = await client.post(
        "/api/v1/negotiation/voice",
        headers={"Authorization": f"Bearer {token}"},
        data={"session_id": "any"},
        files={"audio": ("voice.webm", b"FAKE", "audio/webm")},
    )
    assert r.status_code == 403