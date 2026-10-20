import asyncio
import os

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from vinichannels.adapters.outbound.persistence.database import (
    DEFAULT_DATABASE_URL,
    normalize_database_url,
)
from vinichannels.adapters.outbound.persistence.models import Base

target_metadata = Base.metadata


def run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_with_new_engine() -> None:
    url = normalize_database_url(os.environ.get("VINI_DATABASE_URL", DEFAULT_DATABASE_URL))
    engine = create_async_engine(url, poolclass=pool.NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(run_migrations)
    await engine.dispose()


existing = context.config.attributes.get("connection")
if existing is not None:
    run_migrations(existing)
else:
    asyncio.run(run_with_new_engine())
