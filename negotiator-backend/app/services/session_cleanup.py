# app/services/session_cleanup.py
"""
Background task: mark stale ongoing sessions as interrupted.

Runs inside the FastAPI process via asyncio.create_task.
Checks every SESSION_CLEANUP_INTERVAL_SECONDS, marks sessions whose
last message is older than SESSION_TIMEOUT_MINUTES as interrupted.
"""
import asyncio
import logging
from datetime import datetime, timedelta, UTC

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.negotiation import NegotiationSession, Message
from app.core.constants import SessionStatus
from app.core.config import settings


logger = logging.getLogger(__name__)


async def _cleanup_once(db: AsyncSession | None = None) -> int:
    """
    One pass. Returns the number of sessions marked as interrupted.

    If `db` is None, creates its own session (production path).
    Tests pass their own session explicitly.
    """
    cutoff = datetime.now(UTC) - timedelta(
        minutes=settings.SESSION_TIMEOUT_MINUTES
    )
    marked = 0

    own_session = db is None

    if own_session:
        db = AsyncSessionLocal()
        await db.__aenter__()

    try:
        last_activity = func.coalesce(
            func.max(Message.timestamp),
            NegotiationSession.created_at,
        )

        stmt = (
            select(NegotiationSession)
            .outerjoin(Message, Message.session_id == NegotiationSession.id)
            .where(NegotiationSession.status == SessionStatus.ONGOING)
            .group_by(NegotiationSession.id)
            .having(last_activity < cutoff)
        )
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            session.status = SessionStatus.INTERRUPTED
            session.finished_at = datetime.now(UTC)
            marked += 1

        if marked:
            await db.commit()
    finally:
        if own_session:
            await db.__aexit__(None, None, None)

    return marked


async def cleanup_loop() -> None:
    """
    Runs forever. Started from FastAPI lifespan.
    Catches all exceptions so a single failure does not kill the loop.
    """
    logger.info(
        f"Session cleanup started: "
        f"interval={settings.SESSION_CLEANUP_INTERVAL_SECONDS}s, "
        f"timeout={settings.SESSION_TIMEOUT_MINUTES}min"
    )
    while True:
        try:
            await asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL_SECONDS)
            marked = await _cleanup_once()
            if marked:
                logger.info(f"Marked {marked} stale session(s) as interrupted")
        except asyncio.CancelledError:
            logger.info("Session cleanup cancelled")
            raise
        except Exception as e:
            logger.error(f"Session cleanup error: {e}", exc_info=True)