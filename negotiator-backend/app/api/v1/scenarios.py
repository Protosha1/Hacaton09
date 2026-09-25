# app/api/v1/scenarios.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
import uuid
import secrets

from app.db.session import get_db
from app.models.scenario import Scenario
from app.models.negotiation import NegotiationSession
from app.models.user_added_case import UserAddedCase
from app.models.user import User
from app.schemas.scenario import (
    ScenarioListItem,
    ScenarioDetail,
    ScenarioCreateRequest,
    ScenarioUpdateRequest,
    ScenarioAdminResponse,
    PublishResponse,
    ArchiveResponse,
)
from app.api.v1.auth import require_admin


router = APIRouter()


def _to_admin_response(s: Scenario) -> ScenarioAdminResponse:
    return ScenarioAdminResponse.model_validate(s)


# =========================
# PUBLIC: list & detail
# =========================

@router.get("/", response_model=list[ScenarioListItem])
async def list_scenarios(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Scenario)
        .where(Scenario.admin_id.is_(None))
        .where(Scenario.status == "ready")
    )
    if category == "scenario":
        stmt = stmt.where(Scenario.id.like("scenario-%"))
    elif category:
        stmt = stmt.where(Scenario.category == category)

    result = await db.execute(stmt.order_by(Scenario.name))
    scenarios = result.scalars().all()

    return [
        ScenarioListItem(
            id=s.id, name=s.name, description=s.description,
            category=s.category, user_role=s.user_role,
            opponent_role=s.opponent_role,
        )
        for s in scenarios
    ]


@router.get("/my", response_model=list[ScenarioAdminResponse])
async def list_my_scenarios(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Scenario)
        .where(Scenario.admin_id == admin.id)
        .order_by(Scenario.created_at.desc())
    )
    result = await db.execute(stmt)
    return [_to_admin_response(s) for s in result.scalars().all()]


@router.get("/{scenario_id}", response_model=ScenarioListItem)
async def get_scenario(scenario_id: str, db: AsyncSession = Depends(get_db)):
    """
    Public scenario preview. Returns only spoiler-free fields.
    Only returns scenarios that are:
      - built-in (admin_id IS NULL)
      - in status 'ready'
    """
    scenario = await db.get(Scenario, scenario_id)
    if not scenario or scenario.status != "ready" or scenario.admin_id is not None:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{scenario_id}' not found",
        )

    return ScenarioListItem(
        id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        category=scenario.category,
        user_role=scenario.user_role,
        opponent_role=scenario.opponent_role,
    )


@router.get("/{scenario_id}/admin", response_model=ScenarioAdminResponse)
async def get_scenario_admin(
    scenario_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin view of their own scenario, with all spoiler fields."""
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found")
    if scenario.admin_id != admin.id:
        raise HTTPException(403, detail="You can only view your own scenarios.")
    return _to_admin_response(scenario)


# =========================
# ADMIN: create / update / delete
# =========================

@router.post(
    "/",
    response_model=ScenarioAdminResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_scenario(
    payload: ScenarioCreateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    scenario_id = payload.id or str(uuid.uuid4())

    existing = await db.get(Scenario, scenario_id)
    if existing:
        raise HTTPException(400, f"Scenario with id '{scenario_id}' already exists.")

    scenario = Scenario(
        id=scenario_id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        default_relationship=payload.default_relationship,
        default_power_balance=payload.default_power_balance,
        user_role=payload.user_role,
        user_goal=payload.user_goal,
        opponent_role=payload.opponent_role,
        opponent_character=payload.opponent_character,
        opponent_goal=payload.opponent_goal,
        opponent_interests=payload.opponent_interests,
        opponent_constraints=payload.opponent_constraints,
        opponent_red_lines=payload.opponent_red_lines,
        concession_limits=payload.concession_limits,
        tactics=payload.tactics,
        communication_style=payload.communication_style,
        tone_behavior=payload.tone_behavior,
        non_standard_case=payload.non_standard_case,
        initial_message=payload.initial_message,
        admin_id=admin.id,
        status="draft",
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return _to_admin_response(scenario)


@router.put("/{scenario_id}", response_model=ScenarioAdminResponse)
async def update_scenario(
    scenario_id: str,
    payload: ScenarioUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found")
    if scenario.admin_id != admin.id:
        raise HTTPException(403, detail="You can only edit your own scenarios.")
    if scenario.status == "archived":
        raise HTTPException(400, detail="Cannot edit an archived scenario.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(scenario, field, value)

    await db.commit()
    await db.refresh(scenario)
    return _to_admin_response(scenario)


@router.post("/{scenario_id}/publish", response_model=PublishResponse)
async def publish_scenario(
    scenario_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found")
    if scenario.admin_id != admin.id:
        raise HTTPException(403, detail="You can only publish your own scenarios.")
    if scenario.status == "archived":
        raise HTTPException(400, detail="Cannot publish an archived scenario.")

    # FR-45: all Step 1 fields required
    missing = []
    if not scenario.category:
        missing.append("category")
    if not scenario.name:
        missing.append("name")
    if not scenario.description:
        missing.append("description")
    if not scenario.opponent_role:
        missing.append("opponent_role")
    if not scenario.user_goal:
        missing.append("user_goal")
    if not scenario.opponent_goal:
        missing.append("opponent_goal")

    # FR-46: both Step 2 required fields
    if not scenario.tone_behavior:
        missing.append("tone_behavior")
    if not scenario.concession_limits:
        missing.append("concession_limits")

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish: missing required fields: {', '.join(missing)}.",
        )

    if not scenario.invite_code:
        scenario.invite_code = secrets.token_urlsafe(12)

    scenario.status = "ready"
    await db.commit()
    await db.refresh(scenario)

    return PublishResponse(
        id=scenario.id,
        status=scenario.status,
        invite_code=scenario.invite_code,
        invite_url=f"/invite/{scenario.invite_code}",
    )


@router.post("/{scenario_id}/archive", response_model=ArchiveResponse)
async def archive_scenario(
    scenario_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found")
    if scenario.admin_id != admin.id:
        raise HTTPException(403, detail="You can only archive your own scenarios.")

    scenario.status = "archived"
    await db.commit()
    await db.refresh(scenario)
    return ArchiveResponse(id=scenario.id, status=scenario.status)


@router.delete("/{scenario_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(404, detail=f"Scenario '{scenario_id}' not found")
    if scenario.admin_id != admin.id:
        raise HTTPException(403, detail="You can only delete your own scenarios.")

    # Detach sessions
    await db.execute(
        update(NegotiationSession)
        .where(NegotiationSession.scenario_id == scenario_id)
        .values(scenario_id=None)
    )

    # Remove user_added_cases links (FK cleanup)
    await db.execute(
        delete(UserAddedCase).where(UserAddedCase.case_id == scenario_id)
    )

    await db.delete(scenario)
    await db.commit()
    return None