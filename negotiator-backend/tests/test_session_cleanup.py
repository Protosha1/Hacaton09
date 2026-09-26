# tests/test_session_cleanup.py
"""
Tests for background session auto-timeout.
"""
import pytest
from datetime import datetime, timedelta, UTC

from app.services.session_cleanup import _cleanup_once
from app.models.negotiation import NegotiationSession, Message
from app.core.constants import SessionStatus
from app.core.config import settings


@pytest.mark.asyncio
async def test_cleanup_marks_stale_session(seeded_db):
    """Session with old message and ongoing status -> interrupted."""
    session = NegotiationSession(
        id="stale-1",
        scenario_id="scenario-1",
        user_id="user-1",
        status=SessionStatus.ONGOING,
        role="Seller",
        goal="Sell",
        opponent="Buyer",
        difficulty="beginner",
    )
    seeded_db.add(session)

    # Message older than the timeout threshold
    old_ts = datetime.now(UTC) - timedelta(
        minutes=settings.SESSION_TIMEOUT_MINUTES + 10
    )
    old_msg = Message(
        session_id="stale-1",
        sender="user",
        text="hi",
        timestamp=old_ts,
    )
    seeded_db.add(old_msg)
    await seeded_db.commit()

    marked = await _cleanup_once(seeded_db)
    assert marked >= 1

    await seeded_db.refresh(session)
    assert session.status == SessionStatus.INTERRUPTED
    assert session.finished_at is not None


@pytest.mark.asyncio
async def test_cleanup_keeps_fresh_session(seeded_db):
    """Session with recent message stays ongoing."""
    session = NegotiationSession(
        id="fresh-1",
        scenario_id="scenario-1",
        user_id="user-1",
        status=SessionStatus.ONGOING,
        role="Seller",
        goal="Sell",
        opponent="Buyer",
        difficulty="beginner",
    )
    seeded_db.add(session)

    fresh_ts = datetime.now(UTC) - timedelta(minutes=1)
    fresh_msg = Message(
        session_id="fresh-1",
        sender="user",
        text="hi",
        timestamp=fresh_ts,
    )
    seeded_db.add(fresh_msg)
    await seeded_db.commit()

    await _cleanup_once(seeded_db)
    await seeded_db.refresh(session)
    assert session.status == SessionStatus.ONGOING


@pytest.mark.asyncio
async def test_cleanup_keeps_finished_session(seeded_db):
    """Already finished sessions are not touched."""
    session = NegotiationSession(
        id="done-1",
        scenario_id="scenario-1",
        user_id="user-1",
        status=SessionStatus.FINISHED,
        role="Seller",
        goal="Sell",
        opponent="Buyer",
        difficulty="beginner",
    )
    seeded_db.add(session)
    await seeded_db.commit()

    await _cleanup_once(seeded_db)
    await seeded_db.refresh(session)
    assert session.status == SessionStatus.FINISHED