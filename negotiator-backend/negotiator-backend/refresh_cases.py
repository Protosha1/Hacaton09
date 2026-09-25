# refresh_cases.py
"""
Delete all case-* scenarios so they can be re-seeded with the new category field.
"""
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.scenario import Scenario


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Scenario).where(Scenario.id.like("case-%")))
        cases = result.scalars().all()
        for c in cases:
            await db.delete(c)
        await db.commit()
        print(f"Deleted {len(cases)} case scenarios")


if __name__ == "__main__":
    asyncio.run(main())