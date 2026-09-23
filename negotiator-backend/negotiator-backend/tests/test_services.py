# tests/test_services.py
import pytest
from app.services.negotiation_service import NegotiationService


@pytest.mark.asyncio
async def test_start_session_creates_row(seeded_db):
    service = NegotiationService(seeded_db)
    result = await service.start_session("scenario-1", "user-1")
    assert result["role"] == "Seller"
    assert result["opponent"] == "Buyer"
    assert "session_id" in result


@pytest.mark.asyncio
async def test_process_message_saves_history(seeded_db, mock_llm):
    service = NegotiationService(seeded_db)
    start = await service.start_session("scenario-1", "user-1")
    session_id = start["session_id"]

    result = await service.process_message(session_id, "Hello")
    assert "reply" in result
    assert result["session_status"] == "ongoing"