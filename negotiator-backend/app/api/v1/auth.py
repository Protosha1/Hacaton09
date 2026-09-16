# app/api/v1/auth.py
"""
Authentication endpoints: register, login, me, onboarding.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    OnboardingRequest,
    TokenResponse,
    UserResponse,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


# =========================
# Dependency: current user
# =========================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Read the Bearer token from the Authorization header,
    decode it, and return the corresponding User.
    Raises 401 if the token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a user id.",
        )

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


# =========================
# POST /auth/register
# =========================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    - Prevents duplicate emails.
    - Hashes the password with bcrypt.
    - Returns a JWT token so the user is logged in right away.
    """
    # Check for duplicate email
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # Create the user
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Issue a token immediately
    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


# =========================
# POST /auth/login
# =========================

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate with email + password. Returns a JWT token.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


# =========================
# GET /auth/me
# =========================

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """
    Return the current user's profile.
    Requires a valid Bearer token.
    """
    return UserResponse.model_validate(current_user)


# =========================
# POST /auth/onboarding
# =========================

@router.post("/onboarding", response_model=UserResponse)
async def onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save the user's onboarding choices: 1-3 directions + experience level.
    Marks the user as onboarding_completed = True.
    """
    ALLOWED = {"management", "hiring", "team", "colleagues", "clients", "partners"}
    bad = set(payload.directions) - ALLOWED
    if bad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown directions: {sorted(bad)}. Allowed: {sorted(ALLOWED)}",
        )

    current_user.directions = payload.directions
    current_user.experience_level = payload.experience_level
    current_user.onboarding_completed = True

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)