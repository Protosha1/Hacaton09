# tests/test_analysis_text_blocks.py
"""
Tests for SPIN/BATNA text blocks in the analysis (FR-20, FR-36).
"""
import pytest


@pytest.fixture
def mock_analysis_with_text(monkeypatch):
    from app.services import analysis_service

    async def fake_analyze(session_data, messages):
        return {
            "goal_achieved": "partial",
            "argumentation_score": 60,
            "objection_handling_score": 55,
            "overall_score": 58,
            "spin_score": 45,
            "batna_score": 30,
            "emotion_control_score": 70,
            "spin_analysis": "User asked about the current situation but skipped Implication and Need-payoff questions.",
            "batna_analysis": "User had no visible fallback and argued positions rather than interests.",
            "strengths": ["Clear opening"],
            "weaknesses": ["Missed BATNA"],
            "suggestions": ["Ask more Implication questions"],
            "full_report": "Mock report with text blocks.",
        }

    monkeypatch.setattr(
        analysis_service.AnalysisService, "analyze_session", fake_analyze
    )


@pytest.mark.asyncio
async def test_end_returns_text_blocks(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis_with_text
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
    data = r.json()

    assert data["spin_analysis"] is not None
    assert "situation" in data["spin_analysis"].lower() or "implication" in data["spin_analysis"].lower()
    assert data["batna_analysis"] is not None
    assert "fallback" in data["batna_analysis"].lower() or "interests" in data["batna_analysis"].lower()


@pytest.mark.asyncio
async def test_analysis_endpoint_returns_text_blocks(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis_with_text
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
        json={"session_id": session_id, "message": "Hi"},
    )
    await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=headers,
    )

    r = await client.get(
        f"/api/v1/negotiation/analysis/{session_id}",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["spin_analysis"]
    assert data["batna_analysis"]


@pytest.mark.asyncio
async def test_end_without_text_blocks_still_works(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis
):
    """If LLM doesn't return text blocks, endpoint succeeds with None (backward compat)."""
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
        json={"session_id": session_id, "message": "Hi"},
    )

    r = await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["spin_analysis"] is None
    assert data["batna_analysis"] is None