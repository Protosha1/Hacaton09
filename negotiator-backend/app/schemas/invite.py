# app/schemas/invite.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class InvitePreview(BaseModel):
    """Public preview of an invite (before registration)."""
    code: str
    case_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    user_role: Optional[str] = None
    opponent_role: Optional[str] = None
    user_goal: Optional[str] = None


class InviteAcceptResponse(BaseModel):
    """Returned by POST /invite/{code} after auth."""
    case_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    user_role: Optional[str] = None
    opponent_role: Optional[str] = None
    user_goal: Optional[str] = None
    already_added: bool = False


class AddedCaseItem(BaseModel):
    """One case in the user's personal 'Added' category."""
    case_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    user_role: Optional[str] = None
    opponent_role: Optional[str] = None
    added_at: Optional[datetime] = None


class AddedCasesResponse(BaseModel):
    user_id: str
    total: int
    cases: List[AddedCaseItem]