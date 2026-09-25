# tests/test_transcript_annotations.py
"""
Tests for full transcript annotations (FR-21, FR-37).
"""
import pytest


@pytest.fixture
def mock_analysis_full(monkeypatch):
    """LLM returns full annotations for all USER messages."""
    from app.services import analysis_service

    async def fake_analyze(session_data, messages):
        return {
            "goal_achieved": "partial",
            "argumentation_score": 55,
            "objection_handling_score": 50,
            "overall_score": 52,
            "spin_score": 40,
            "batna_score": 30,
            "emotion_control_score": 60,
            "spin_analysis": "User skipped implication questions.",
            "batna_analysis": "No visible fallback.",
            "transcript_annotations": [
                {
                    "index": 0,
                    "original": "Hello, I want to discuss a raise.",
                    "type": "strong",
                    "category": "opening",
                    "why": "Clear and direct opening.",
                    "suggestion": None,
                },
                {
                    "index": 2,
                    "original": "You must raise my salary.",
                    "type": "weak",
                    "category": "directive",
                    "why": "Directive and without justification.",
                    "suggestion": "I'd like to discuss a raise - here are my results.",
                },
                {
                    "index": 4,
                    "original": "Okay, maybe next quarter.",
                    "type": "weak",
                    "category": "concession",
                    "why": "Gave up too easily.",
                    "suggestion": "Let's agree on concrete criteria and a timeline.",
                },
            ],
            "strengths": ["Clear opening"],
            "weaknesses": ["Emotional"],
            "suggestions": ["Prepare arguments"],
            "full_report": "Mock report.",
        }

    monkeypatch.setattr(
        analysis_service.AnalysisService, "analyze_session", fake_analyze
    )


@pytest.fixture
def mock_analysis_malformed(monkeypatch):
    """LLM returns annotations with some malformed / out-of-range items."""
    from app.services import analysis_service

    async def fake_analyze(session_data, messages):
        return {
            "goal_achieved": "partial",
            "argumentation_score": 50,
            "objection_handling_score": 50,
            "overall_score": 50,
            "spin_score": 50,
            "batna_score": 50,
            "emotion_control_score": 50,
            "spin_analysis": "...",
            "batna_analysis": "...",
            "transcript_annotations": [
                {
                    "index": 0,
                    "original": "Good",
                    "type": "strong",
                    "category": "opening",
                    "why": "ok",
                    "suggestion": "should-be-dropped",
                },
                {"missing_fields": True},
                "not a dict",
                {
                    "index": 999,
                    "original": "Ghost",
                    "type": "weak",
                    "category": "other",
                    "why": "x",
                    "suggestion": "y",
                },
                {
                    "index": 1,
                    "original": "Hmm",
                    "type": "neutral",
                    "category": "other",
                    "why": "just filler",
                    "suggestion": None,
                },
            ],
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "full_report": "...",
        }

    monkeypatch.setattr(
        analysis_service.AnalysisService, "analyze_session", fake_analyze
    )


# =========================
# Tests
# =========================

@pytest.mark.asyncio
async def test_end_returns_full_annotations(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis_full
):
    headers = auth_headers_factory(user_1_token)

    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    for text in ["Hello, I want to discuss a raise.",
                 "You must raise my salary.",
                 "Okay, maybe next quarter."]:
        await client.post(
            "/api/v1/negotiation/message",
            headers=headers,
            json={"session_id": session_id, "message": text},
        )

    r = await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()

    anns = data["transcript_annotations"]
    assert isinstance(anns, list)
    assert len(anns) >= 1
    indices = [a["index"] for a in anns]
    assert indices == sorted(indices)
    strong_items = [a for a in anns if a["type"] == "strong"]
    for s in strong_items:
        assert s["suggestion"] is None

    assert data["strong_count"] >= 0
    assert data["weak_count"] >= 0
    assert data["neutral_count"] >= 0


@pytest.mark.asyncio
async def test_end_drops_malformed_annotations(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis_malformed
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
        "/api/v1/negotiation/message",
        headers=headers,
        json={"session_id": session_id, "message": "Hmm"},
    )

    r = await client.post(
        f"/api/v1/negotiation/end?session_id={session_id}",
        headers=headers,
    )
    assert r.status_code == 200
    anns = r.json()["transcript_annotations"]
    indices = sorted(a["index"] for a in anns)
    assert indices == [0, 1]
    strong = next(a for a in anns if a["type"] == "strong")
    assert strong["suggestion"] is None


@pytest.mark.asyncio
async def test_analysis_endpoint_returns_annotations(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis_full
):
    headers = auth_headers_factory(user_1_token)

    r = await client.post(
        "/api/v1/negotiation/start",
        headers=headers,
        json={"scenario_id": "scenario-1", "user_id": "user-1"},
    )
    session_id = r.json()["session_id"]

    for text in ["Hello", "You must raise my salary.", "Okay, maybe next quarter."]:
        await client.post(
            "/api/v1/negotiation/message",
            headers=headers,
            json={"session_id": session_id, "message": text},
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
    assert "transcript_annotations" in data
    assert isinstance(data["transcript_annotations"], list)


@pytest.mark.asyncio
async def test_end_without_annotations_key(
    client, seeded_db, user_1_token, auth_headers_factory, mock_llm, mock_analysis
):
    """Old mock_analysis has no transcript_annotations key - returns []."""
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
    assert data["transcript_annotations"] == []
    assert data["strong_count"] == 0
    assert data["weak_count"] == 0
    assert data["neutral_count"] == 0