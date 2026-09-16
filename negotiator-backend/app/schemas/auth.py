# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Literal


# =========================
# Requests
# =========================

class RegisterRequest(BaseModel):
    """Data for POST /auth/register."""
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., min_length=6, examples=["secret123"])
    name: Optional[str] = Field(None, examples=["Ivan Petrov"])


class LoginRequest(BaseModel):
    """Data for POST /auth/login."""
    email: EmailStr = Field(..., examples=["user@example.com"])
    password: str = Field(..., examples=["secret123"])


class OnboardingRequest(BaseModel):
    """Data for POST /auth/onboarding."""
    directions: List[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        examples=[["management", "hiring"]],
        description="1-3 directions out of: management, hiring, team, colleagues, clients, partners",
    )
    experience_level: Literal["beginner", "practitioner", "expert"] = Field(
        ...,
        examples=["beginner"],
    )


# =========================
# Responses
# =========================

class TokenResponse(BaseModel):
    """Returned by /auth/login and /auth/register."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user info. Never exposes the password hash."""
    id: str
    email: str
    name: Optional[str] = None
    onboarding_completed: bool
    directions: Optional[List[str]] = None
    experience_level: str

    class Config:
        from_attributes = True  # allows reading from SQLAlchemy objects