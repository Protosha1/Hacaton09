# app/db/session.py
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Naming convention for constraints.
# Lets Alembic know the names of FKs / PKs / UQs, so future migrations
# can drop them cleanly (SQLite does not support ALTER TABLE ADD CONSTRAINT).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base(metadata=MetaData(naming_convention=NAMING_CONVENTION))


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session