# app/schemas/scenario.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# =========================
# Public (GET)
# =========================

class ScenarioListItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    user_role: Optional[str] = None
    opponent_role: Optional[str] = None


class ScenarioDetail(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    default_relationship: Optional[str] = None
    default_power_balance: Optional[str] = None

    user_role: Optional[str] = None
    user_goal: Optional[str] = None

    opponent_role: Optional[str] = None
    opponent_character: Optional[str] = None
    opponent_goal: Optional[str] = None
    opponent_interests: Optional[List[str]] = None
    opponent_constraints: Optional[List[str]] = None
    opponent_red_lines: Optional[List[str]] = None

    concession_limits: Optional[Dict[str, Any]] = None
    tactics: Optional[List[str]] = None
    communication_style: Optional[str] = None
    initial_message: Optional[str] = None


# =========================
# Admin CRUD
# =========================

class ScenarioCreateRequest(BaseModel):
    """Request for POST /scenarios/ (admin only)."""
    id: Optional[str] = Field(
        None, examples=["custom-negotiation-1"],
        description="Optional custom ID. Leave empty for UUID.",
    )
    name: str = Field(..., examples=["Переговоры о лицензии"])
    description: Optional[str] = None
    category: Optional[str] = Field(
        None, examples=["partners"],
        description="management | hiring | team | colleagues | clients | partners",
    )
    default_relationship: Optional[str] = None
    default_power_balance: Optional[str] = None

    user_role: Optional[str] = None
    user_goal: Optional[str] = None

    opponent_role: Optional[str] = None
    opponent_character: Optional[str] = None
    opponent_goal: Optional[str] = None
    opponent_interests: Optional[List[str]] = None
    opponent_constraints: Optional[List[str]] = None
    opponent_red_lines: Optional[List[str]] = None

    concession_limits: Optional[Dict[str, Any]] = None
    tactics: Optional[List[str]] = None
    communication_style: Optional[str] = None

    # FR-46: admin-specific fields
    tone_behavior: Optional[str] = Field(
        None,
        examples=["Жёсткий, но справедливый"],
        description="Обязательное для publish. Тон/поведение оппонента.",
    )
    non_standard_case: Optional[str] = Field(
        None,
        examples=["Оппонент внезапно меняет условия"],
        description="Опциональное осложнение.",
    )

    initial_message: Optional[str] = None


class ScenarioUpdateRequest(BaseModel):
    """Request for PUT /scenarios/{id}. All fields optional."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    default_relationship: Optional[str] = None
    default_power_balance: Optional[str] = None

    user_role: Optional[str] = None
    user_goal: Optional[str] = None

    opponent_role: Optional[str] = None
    opponent_character: Optional[str] = None
    opponent_goal: Optional[str] = None
    opponent_interests: Optional[List[str]] = None
    opponent_constraints: Optional[List[str]] = None
    opponent_red_lines: Optional[List[str]] = None

    concession_limits: Optional[Dict[str, Any]] = None
    tactics: Optional[List[str]] = None
    communication_style: Optional[str] = None

    tone_behavior: Optional[str] = None
    non_standard_case: Optional[str] = None

    initial_message: Optional[str] = None


class ScenarioAdminResponse(BaseModel):
    """Returned by admin endpoints. Includes status/invite_code/admin_id."""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    default_relationship: Optional[str] = None
    default_power_balance: Optional[str] = None

    user_role: Optional[str] = None
    user_goal: Optional[str] = None

    opponent_role: Optional[str] = None
    opponent_character: Optional[str] = None
    opponent_goal: Optional[str] = None
    opponent_interests: Optional[List[str]] = None
    opponent_constraints: Optional[List[str]] = None
    opponent_red_lines: Optional[List[str]] = None

    concession_limits: Optional[Dict[str, Any]] = None
    tactics: Optional[List[str]] = None
    communication_style: Optional[str] = None

    tone_behavior: Optional[str] = None
    non_standard_case: Optional[str] = None

    initial_message: Optional[str] = None

    # Admin metadata
    admin_id: Optional[str] = None
    status: str = "ready"           # draft | ready | archived
    invite_code: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PublishResponse(BaseModel):
    """Returned by POST /scenarios/{id}/publish."""
    id: str
    status: str
    invite_code: str
    invite_url: str


class ArchiveResponse(BaseModel):
    """Returned by POST /scenarios/{id}/archive."""
    id: str
    status: str