# app/schemas/negotiation.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class StartNegotiationRequest(BaseModel):
    scenario_id: str = Field(..., examples=["scenario-1"])
    user_id: Optional[str] = Field(None, examples=["user-1"])
    difficulty: Optional[Literal["beginner", "practitioner", "expert"]] = Field(
        None,
        examples=["practitioner"],
        description="If not provided, uses the user's experience_level from onboarding.",
    )
    relationship: Optional[Literal["stranger", "colleague", "friend", "boss", "subordinate"]] = Field(
        None,
        examples=["colleague"],
        description="Override the scenario's default relationship.",
    )
    power_balance: Optional[Literal["user_strong", "equal", "opponent_strong"]] = Field(
        None,
        examples=["equal"],
        description="Override the scenario's default power balance.",
    )


class MessageRequest(BaseModel):
    session_id: str = Field(..., examples=["5b7ba051-189b-4fe3-9f82-aebc28feedf1"])
    message: str = Field(..., examples=["Our price is $1200 per unit."])


class AnalysisResponse(BaseModel):
    session_id: str
    goal_achieved: str
    argumentation_score: int
    objection_handling_score: int
    overall_score: int
    spin_score: Optional[int] = None
    batna_score: Optional[int] = None
    emotion_control_score: Optional[int] = None
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    full_report: str


class SessionListItem(BaseModel):
    session_id: str
    scenario_id: Optional[str] = None
    scenario_name: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    opponent: Optional[str] = None
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    overall_score: Optional[int] = None


class SessionMessageItem(BaseModel):
    sender: str
    text: str
    timestamp: datetime


class AnalysisListItem(BaseModel):
    session_id: str
    overall_score: int
    goal_achieved: str
    created_at: datetime