# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db


router = APIRouter()


@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    Verifies that the API is running and the database is reachable.
    """
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "unreachable",
    }