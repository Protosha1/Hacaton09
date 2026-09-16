# app/schemas/scenario.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ScenarioListItem(BaseModel):
    """Short info shown on the scenario selection cards."""
    id: str
    name: str
    description: Optional[str] = None
    user_role: Optional[str] = None
    opponent_role: Optional[str] = None


class ScenarioDetail(BaseModel):
    """Full scenario info, including 'spoilers' (opponent goals, tactics, limits)."""
    id: str
    name: str
    description: Optional[str] = None
    default_relationship: Optional[str] = None      # новое
    default_power_balance: Optional[str] = None 

    # User's public info
    user_role: Optional[str] = None
    user_goal: Optional[str] = None
    # Opponent info (may be considered 'spoilers')
    opponent_role: Optional[str] = None
    opponent_character: Optional[str] = None
    opponent_goal: Optional[str] = None
    opponent_interests: Optional[List[str]] = None
    opponent_constraints: Optional[List[str]] = None
    opponent_red_lines: Optional[List[str]] = None
    concession_limits: Optional[Dict[str, Any]] = None
    tactics: Optional[List[str]] = None
    communication_style: Optional[str] = None

    # Opening message
    initial_message: Optional[str] = None