# seed_admin.py
"""
Create or update the first admin user.

Reads ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME from .env (via settings).

Usage:
    python seed_admin.py

Behaviour:
- If no user with ADMIN_EMAIL exists  -> creates one with role='admin'.
- If user exists                       -> updates their password and role to 'admin'.
"""
import asyncio
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.config import settings
from app.core.security import hash_password


async def seed_admin():
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
                role="admin",
                onboarding_completed=True,   # админ онбординг не проходит
                directions=["management", "hiring", "team",
                            "colleagues", "clients", "partners"],
                experience_level="expert",
            )
            db.add(user)
            print(f"[OK] Admin created: {settings.ADMIN_EMAIL}")
        else:
            user.role = "admin"
            user.hashed_password = hash_password(settings.ADMIN_PASSWORD)
            if settings.ADMIN_NAME:
                user.name = settings.ADMIN_NAME
            print(f"[OK] Admin updated: {settings.ADMIN_EMAIL}")

        await db.commit()
        print(f"[INFO] Role: admin")
        print(f"[INFO] Password: {settings.ADMIN_PASSWORD}")
        print("")
        print("Login via POST /api/v1/auth/login with this email and password.")


if __name__ == "__main__":
    asyncio.run(seed_admin())