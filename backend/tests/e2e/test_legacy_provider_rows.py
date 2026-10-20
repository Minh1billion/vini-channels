import asyncio

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("aiosqlite")

from vinichannels.adapters.outbound.persistence.database import (
    create_engine,
    create_session_factory,
    migrate_to_head,
)
from vinichannels.adapters.outbound.persistence.models import ProviderConfigModel
from vinichannels.adapters.outbound.persistence.repositories import SqlProviderConfigRepository
from vinichannels.domain.syncing.providers import ProviderKey


def test_list_all_ignores_provider_rows_of_removed_sources() -> None:

    async def scenario() -> list[ProviderKey]:
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        await migrate_to_head(engine)
        factory = create_session_factory(engine)
        async with factory() as session:
            session.add(ProviderConfigModel(key="mock", enabled=True, priority=90))
            session.add(ProviderConfigModel(key="apify", enabled=False, priority=30))
            await session.commit()
        async with factory() as session:
            configs = await SqlProviderConfigRepository(session).list_all()
        await engine.dispose()
        return [config.key for config in configs]

    assert asyncio.run(scenario()) == [ProviderKey.APIFY]
