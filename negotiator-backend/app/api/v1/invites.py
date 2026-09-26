# app/api/v1/invites.py
"""
Invite endpoints (FR-48, FR-49).
Public preview + authenticated accept.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.scenario import Scenario
from app.models.user import User
from app.models.user_added_case import UserAddedCase
from app.schemas.invite import InvitePreview, InviteAcceptResponse
from app.api.v1.auth import require_user


router = APIRouter()


def _check_ready(scenario: Scenario) -> None:
    """Raise the appropriate HTTP error if the scenario is not invitable."""
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found.",
        )
    if scenario.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This training is no longer active.",
        )
    if scenario.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found.",
        )


async def _find_scenario_by_code(db: AsyncSession, code: str) -> Scenario:
    result = await db.execute(
        select(Scenario).where(Scenario.invite_code == code)
    )
    return result.scalar_one_or_none()


# =========================
# GET /invite/{code} — public preview
# =========================

@router.get("/{code}", response_model=InvitePreview)
async def preview_invite(code: str, db: AsyncSession = Depends(get_db)):
    """
    Public preview of an invite. No auth required.
    Used by the frontend before registration, to show what the case is about.
    """
    scenario = await _find_scenario_by_code(db, code)
    _check_ready(scenario)

    return InvitePreview(
        code=code,
        case_id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        category=scenario.category,
        user_role=scenario.user_role,
        opponent_role=scenario.opponent_role,
        user_goal=scenario.user_goal,
    )


# =========================
# POST /invite/{code} — accept (auth required)
# =========================

@router.post("/{code}", response_model=InviteAcceptResponse)
async def accept_invite(
    code: str,
    user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept an invite. Creates UserAddedCase (idempotent).
    Returns the scenario payload for the Constructor pre-fill.
    """
    scenario = await _find_scenario_by_code(db, code)
    _check_ready(scenario)

    # Check if already added
    existing = await db.execute(
        select(UserAddedCase)
        .where(UserAddedCase.user_id == user.id)
        .where(UserAddedCase.case_id == scenario.id)
    )
    already = existing.scalar_one_or_none()

    if already is None:
        db.add(UserAddedCase(user_id=user.id, case_id=scenario.id))
        await db.commit()

    return InviteAcceptResponse(
        case_id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        category=scenario.category,
        user_role=scenario.user_role,
        opponent_role=scenario.opponent_role,
        user_goal=scenario.user_goal,
        already_added=already is not None,
    )