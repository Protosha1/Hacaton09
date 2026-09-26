# app/schemas/recommendation.py
from pydantic import BaseModel
from typing import Optional, List


class RecommendedCase(BaseModel):
    case_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    user_role: Optional[str] = None
    opponent_role: Optional[str] = None


class RecommendationsResponse(BaseModel):
    user_id: str
    total: int
    recommendations: List[RecommendedCase]