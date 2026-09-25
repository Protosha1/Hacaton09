# alembic/env.py
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Ensure project root is on sys.path, regardless of CWD
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# Use the same DB URL as the app
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

from app.db.base import Base
target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    SQLite does not support ALTER TABLE ADD/DROP CONSTRAINT.
    Skip FK/UQ constraint ops from autogenerate.

    Warning: this also disables autogenerate for FK/UQ changes on EXISTING
    tables. If you later add/rename a FK on an existing model, autogenerate
    will report "no changes" - write the migration manually.
    """
    if type_ in ("foreign_key_constraint", "unique_constraint"):
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()