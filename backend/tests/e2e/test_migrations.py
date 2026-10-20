import asyncio
from pathlib import Path

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("aiosqlite")
pytest.importorskip("alembic")

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection

from vinichannels.adapters.outbound.persistence.database import (
    MIGRATIONS_DIR,
    create_engine,
    migrate_to_head,
)
from vinichannels.adapters.outbound.persistence.models import Base


def _head() -> str | None:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    return ScriptDirectory.from_config(config).get_current_head()


def _url(tmp_path: Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


def _drift(connection: Connection) -> list[object]:
    context = MigrationContext.configure(connection, opts={"compare_type": True})
    return list(compare_metadata(context, Base.metadata))


def _table_names(connection: Connection) -> set[str]:
    return set(inspect(connection).get_table_names())


def test_migrate_creates_every_model_table_and_matches_models(tmp_path: Path) -> None:
    async def scenario() -> tuple[set[str], list[object], str | None]:
        engine = create_engine(_url(tmp_path))
        await migrate_to_head(engine)
        async with engine.connect() as connection:
            tables = await connection.run_sync(_table_names)
            drift = await connection.run_sync(_drift)
            version = (
                await connection.execute(text("select version_num from alembic_version"))
            ).scalar_one_or_none()
        await engine.dispose()
        return tables, drift, version

    tables, drift, version = asyncio.run(scenario())
    assert set(Base.metadata.tables) <= tables
    assert drift == []
    assert version is not None


def test_migrate_twice_is_a_no_op(tmp_path: Path) -> None:
    async def scenario() -> int:
        engine = create_engine(_url(tmp_path))
        await migrate_to_head(engine)
        await migrate_to_head(engine)
        async with engine.connect() as connection:
            rows = (
                await connection.execute(text("select count(*) from alembic_version"))
            ).scalar_one()
        await engine.dispose()
        return int(rows)

    assert asyncio.run(scenario()) == 1


def test_database_created_without_alembic_is_stamped_and_keeps_data(tmp_path: Path) -> None:
    async def scenario() -> tuple[str, str]:
        engine = create_engine(_url(tmp_path))
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
            await connection.execute(
                text(
                    "insert into users (id, email, password_hash, role, is_active) "
                    "values ('u1', 'a@b.co', 'hash', 'admin', 1)"
                )
            )
        await migrate_to_head(engine)
        async with engine.connect() as connection:
            email = (await connection.execute(text("select email from users"))).scalar_one()
            version = (
                await connection.execute(text("select version_num from alembic_version"))
            ).scalar_one()
        await engine.dispose()
        return str(email), str(version)

    email, version = asyncio.run(scenario())
    assert email == "a@b.co"
    assert version == _head()
