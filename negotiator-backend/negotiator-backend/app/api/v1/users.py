# app/api/v1/users.py
"""
User-scoped endpoints: skills, recommendations, interrupted session, added cases.
All endpoints enforce that user_id matches the authenticated user (FR-19).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.user import User
from app.models.skill_progress import SkillProgress
from app.models.negotiation import NegotiationSession, Message
from app.models.scenario import Scenario
from app.models.user_added_case import UserAddedCase
from app.schemas.skill import SkillItem, UserSkillsResponse
from app.schemas.negotiation import InterruptedSessionInfo, InterruptedSessionResponse
from app.schemas.invite import AddedCaseItem, AddedCasesResponse
from app.schemas.recommendation import RecommendedCase, RecommendationsResponse
from app.api.v1.auth import require_user
from app.core.skills import METRICS
from app.core.constants import SessionStatus


router = APIRouter()


def _ensure_own(user_id: str, user: User) -> None:
    """Raise 403 if the requested user_id is not the authenticated user."""
    if user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own data.",
        )


# =========================
# GET /users/{user_id}/skills
# =========================

@router.get("/{user_id}/skills", response_model=UserSkillsResponse)
async def get_user_skills(
    user_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_own(user_id, user)

    result = await db.execute(
        select(SkillProgress).where(SkillProgress.user_id == user_id)
    )
    rows = {r.metric: r for r in result.scalars().all()}

    skills = []
    for metric in METRICS:
        row = rows.get(metric)
        if row:
            skills.append(SkillItem(
                metric=row.metric,
                current_value=row.current_value,
                sessions_count=row.sessions_count,
                history=row.history,
                updated_at=row.updated_at,
            ))
        else:
            skills.append(SkillItem(
                metric=metric,
                current_value=0,
                sessions_count=0,
                history=[],
                updated_at=None,
            ))

    return UserSkillsResponse(user_id=user_id, skills=skills)


# =========================
# GET /users/{user_id}/recommendations
# =========================

@router.get("/{user_id}/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    user_id: str,
    limit: int = 10,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_own(user_id, user)

    directions = user.directions or []
    if not directions:
        return RecommendationsResponse(user_id=user_id, total=0, recommendations=[])

    # IDs already played by the user
    played_q = await db.execute(
        select(NegotiationSession.scenario_id)
        .where(NegotiationSession.user_id == user_id)
        .where(NegotiationSession.scenario_id.is_not(None))
        .distinct()
    )
    played_ids = {row[0] for row in played_q.all()}

    # Public scenarios in user's categories
    stmt = (
        select(Scenario)
        .where(Scenario.admin_id.is_(None))
        .where(Scenario.status == "ready")
        .where(Scenario.category.in_(directions))
        .order_by(Scenario.name)
    )
    result = await db.execute(stmt)
    all_scenarios = list(result.scalars().all())

    fresh = [s for s in all_scenarios if s.id not in played_ids]
    pool = fresh if fresh else all_scenarios
    pool = pool[:limit]

    return RecommendationsResponse(
        user_id=user_id,
        total=len(pool),
        recommendations=[
            RecommendedCase(
                case_id=s.id,
                name=s.name,
                description=s.description,
                category=s.category,
                user_role=s.user_role,
                opponent_role=s.opponent_role,
            )
            for s in pool
        ],
    )


# =========================
# GET /users/{user_id}/interrupted-session
# =========================

@router.get("/{user_id}/interrupted-session", response_model=InterruptedSessionResponse)
async def get_interrupted_session(
    user_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_own(user_id, user)

    stmt = (
        select(NegotiationSession, Scenario.name)
        .outerjoin(Scenario, Scenario.id == NegotiationSession.scenario_id)
        .where(NegotiationSession.user_id == user_id)
        .where(NegotiationSession.status == SessionStatus.INTERRUPTED)
        .order_by(NegotiationSession.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        return InterruptedSessionResponse(has_interrupted=False, session=None)

    session, scenario_name = row

    msg_count_res = await db.execute(
        select(func.count(Message.id)).where(Message.session_id == session.id)
    )
    msg_count = msg_count_res.scalar() or 0

    info = InterruptedSessionInfo(
        session_id=session.id,
        scenario_id=session.scenario_id,
        scenario_name=scenario_name,
        role=session.role,
        goal=session.goal,
        difficulty=session.difficulty,
        relationship=session.relationship,
        power_balance=session.power_balance,
        created_at=session.created_at,
        finished_at=session.finished_at,
        messages_count=msg_count,
    )

    return InterruptedSessionResponse(has_interrupted=True, session=info)


# =========================
# GET /users/{user_id}/added-cases
# =========================

@router.get("/{user_id}/added-cases", response_model=AddedCasesResponse)
async def get_added_cases(
    user_id: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    _ensure_own(user_id, user)

    stmt = (
        select(UserAddedCase, Scenario)
        .join(Scenario, Scenario.id == UserAddedCase.case_id)
        .where(UserAddedCase.user_id == user_id)
        .order_by(UserAddedCase.added_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = [
        AddedCaseItem(
            case_id=sc.id,
            name=sc.name,
            description=sc.description,
            category=sc.category,
            user_role=sc.user_role,
            opponent_role=sc.opponent_role,
            added_at=link.added_at,
        )
        for link, sc in rows
    ]

    return AddedCasesResponse(
        user_id=user_id,
        total=len(items),
        cases=items,
    )