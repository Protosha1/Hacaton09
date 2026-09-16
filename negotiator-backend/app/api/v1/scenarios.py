# app/api/v1/scenarios.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioListItem, ScenarioDetail
from typing import Optional 

router = APIRouter()


@router.get("/", response_model=list[ScenarioListItem])
async def list_scenarios(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Return a list of scenarios, optionally filtered by category.

    Available categories:
      management, hiring, team, colleagues, clients, partners
    Pass category=scenario to get the 3 legacy demo scenarios.
    """
    stmt = select(Scenario)

    if category == "scenario":
        stmt = stmt.where(Scenario.id.like("scenario-%"))
    elif category:
        stmt = stmt.where(Scenario.category == category)

    result = await db.execute(stmt.order_by(Scenario.name))
    scenarios = result.scalars().all()

    return [
        ScenarioListItem(
            id=s.id,
            name=s.name,
            description=s.description,
            user_role=s.user_role,
            opponent_role=s.opponent_role,
        )
        for s in scenarios
    ]


@router.get("/{scenario_id}", response_model=ScenarioDetail)
async def get_scenario(scenario_id: str, db: AsyncSession = Depends(get_db)):
    """
    Return full details for a single scenario.
    Includes spoiler fields such as opponent goals, tactics, and limits.
    The frontend can decide whether to show them to the user.
    """
    scenario = await db.get(Scenario, scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario '{scenario_id}' not found"
        )

    return ScenarioDetail(
        id=scenario.id,
        name=scenario.name,
        description=scenario.description,
        user_role=scenario.user_role,
        user_goal=scenario.user_goal,
        opponent_role=scenario.opponent_role,
        opponent_character=scenario.opponent_character,
        opponent_goal=scenario.opponent_goal,
        opponent_interests=scenario.opponent_interests,
        opponent_constraints=scenario.opponent_constraints,
        opponent_red_lines=scenario.opponent_red_lines,
        concession_limits=scenario.concession_limits,
        tactics=scenario.tactics,
        communication_style=scenario.communication_style,
        initial_message=scenario.initial_message,
    )