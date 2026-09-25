# app/core/skills.py
"""
Skill progress update logic (FR-24).

Formula: new_value = old_value * 0.7 + session_score * 0.3
This is an exponential moving average, giving smooth growth.

Metrics: emotion_control, batna, spin
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill_progress import SkillProgress


METRICS = ["emotion_control", "batna", "spin"]

# Weight of history vs new session
HISTORY_WEIGHT = 0.7
SESSION_WEIGHT = 0.3

MAX_HISTORY_LEN = 50


async def update_skills_for_user(
    db: AsyncSession,
    user_id: str,
    scores: dict,
) -> None:
    """
    Update all skill metrics for a user based on a new session's scores.

    `scores` must contain: emotion_control_score, batna_score, spin_score.
    Missing values default to 0.
    """
    # Map score keys -> metric names
    score_map = {
        "emotion_control": "emotion_control_score",
        "batna": "batna_score",
        "spin": "spin_score",
    }

    for metric, score_key in score_map.items():
        session_score = int(scores.get(score_key, 0) or 0)
        # Clamp to 0-100
        session_score = max(0, min(100, session_score))

        # Find existing record
        result = await db.execute(
            select(SkillProgress)
            .where(SkillProgress.user_id == user_id)
            .where(SkillProgress.metric == metric)
        )
        row = result.scalar_one_or_none()

        if row is None:
            # First session for this metric  initialize with the score
            new_value = session_score
            history = [session_score]
            row = SkillProgress(
                user_id=user_id,
                metric=metric,
                current_value=new_value,
                sessions_count=1,
                history=history,
            )
            db.add(row)
        else:
            old = row.current_value or 0
            new_value = int(round(old * HISTORY_WEIGHT + session_score * SESSION_WEIGHT))
            row.current_value = new_value
            row.sessions_count = (row.sessions_count or 0) + 1

            history = list(row.history or [])
            history.append(session_score)
            # Keep only last N
            if len(history) > MAX_HISTORY_LEN:
                history = history[-MAX_HISTORY_LEN:]
            row.history = history

    # Commit is done by caller