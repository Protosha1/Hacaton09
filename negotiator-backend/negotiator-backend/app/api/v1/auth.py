# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, OnboardingRequest,
    TokenResponse, UserResponse,
    AdminRegisterRequest, AdminLoginRequest,
)
from app.core.security import (
    hash_password, verify_password,
    create_access_token, decode_access_token,
)
from app.core.xp import get_rank
from app.core.constants import UserRole, UserStatus, Direction


router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


def _user_to_response(user: User) -> UserResponse:
    rank = get_rank(user.total_xp or 0)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role=user.role,
        status=user.status,
        onboarding_completed=user.onboarding_completed,
        directions=user.directions,
        experience_level=user.experience_level,
        total_xp=user.total_xp or 0,
        rank_level=rank["level"],
        rank_name=rank["name"],
        consent_given=bool(user.consent_given),
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
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
        raise HTTPException(401, "Token does not contain a user id.")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(401, "User not found.")
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(403, "Admin access required.")
    return current_user


async def require_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role == UserRole.ADMIN:
        raise HTTPException(403, "Administrators have no access to user endpoints.")
    return current_user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not payload.consent_given:
        raise HTTPException(400, "Consent to personal data processing is required.")
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "A user with this email already exists.")
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role=UserRole.USER,
        status=UserStatus.PENDING_ONBOARDING,
        onboarding_completed=False,
        total_xp=0,
        consent_given=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=create_access_token({"sub": user.id}))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password.")
    return TokenResponse(access_token=create_access_token({"sub": user.id}))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(require_user)):
    return _user_to_response(current_user)


@router.post("/onboarding", response_model=UserResponse)
async def onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    bad = set(payload.directions) - Direction.ALL
    if bad:
        raise HTTPException(400, f"Unknown directions: {sorted(bad)}.")
    current_user.directions = payload.directions
    current_user.experience_level = payload.experience_level
    current_user.onboarding_completed = True
    current_user.status = UserStatus.ACTIVE
    await db.commit()
    await db.refresh(current_user)
    return _user_to_response(current_user)


@router.post("/register/admin", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_admin(payload: AdminRegisterRequest, db: AsyncSession = Depends(get_db)):
    if not payload.consent_given:
        raise HTTPException(400, "Consent to personal data processing is required.")
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "A user with this email already exists.")
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        onboarding_completed=True,
        directions=[],
        experience_level="expert",
        total_xp=0,
        consent_given=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=create_access_token({"sub": user.id}))


@router.post("/login/admin", response_model=TokenResponse)
async def login_admin(payload: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password.")
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, "This account is not an administrator.")
    return TokenResponse(access_token=create_access_token({"sub": user.id}))