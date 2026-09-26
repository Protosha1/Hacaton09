# seed_admin.py
"""
Create or update the first admin user.

Reads ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME from .env (via settings).

Usage:
    python seed_admin.py
"""
import asyncio
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.config import settings
from app.core.security import hash_password
from app.core.constants import UserRole, UserStatus


async def seed_admin():
    if not settings.ADMIN_PASSWORD or len(settings.ADMIN_PASSWORD) < 12:
        raise SystemExit(
            "ADMIN_PASSWORD is not set or is too short (min 12 chars). "
            "Set it in .env before running seed_admin.py."
        )

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                email=settings.ADMIN_EMAIL,
                name=settings.ADMIN_NAME,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                onboarding_completed=True,
                directions=["management", "hiring", "team",
                            "colleagues", "clients", "partners"],
                experience_level="expert",
                consent_given=True,
            )
            db.add(user)
            print(f"[OK] Admin created: {settings.ADMIN_EMAIL}")
        else:
            user.role = UserRole.ADMIN
            user.status = UserStatus.ACTIVE
            user.onboarding_completed = True
            user.consent_given = True
            user.hashed_password = hash_password(settings.ADMIN_PASSWORD)
            if settings.ADMIN_NAME:
                user.name = settings.ADMIN_NAME
            print(f"[OK] Admin updated: {settings.ADMIN_EMAIL}")

        await db.commit()
        print(f"[INFO] Role: admin")
        print(f"[INFO] Password set for {settings.ADMIN_EMAIL}")
        print("")
        print("Login via POST /api/v1/auth/login/admin")


if __name__ == "__main__":
    asyncio.run(seed_admin())