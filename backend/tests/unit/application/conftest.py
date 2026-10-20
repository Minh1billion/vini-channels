import asyncio
from collections.abc import Coroutine
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from vinichannels.adapters.outbound.memory.unit_of_work import MemoryUnitOfWorkFactory
from vinichannels.application.dto import ChannelDTO
from vinichannels.domain.channels.entities import Channel
from vinichannels.domain.channels.value_objects import Handle
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.shared.ids import ChannelId, PartnerId, UserId, new_id


class FixedClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 10, 19, 7, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current


class PlainHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class DictTokens:
    def __init__(self) -> None:
        self.issued: dict[str, UserId] = {}

    def issue(self, user_id: UserId) -> str:
        token = f"token-{user_id}"
        self.issued[token] = user_id
        return token

    def verify(self, token: str) -> UserId | None:
        return self.issued.get(token)


@dataclass
class World:
    uow: MemoryUnitOfWorkFactory
    clock: FixedClock
    hasher: PlainHasher
    tokens: DictTokens

    def user(self, role: Role, email: str | None = None) -> User:
        user = User(
            id=UserId(new_id()),
            email=email or f"{role.value}-{new_id()[:6]}@example.com",
            role=role,
            password_hash=self.hasher.hash("password123"),
        )
        self.uow.state.users[user.id] = user
        return user


@pytest.fixture
def world() -> World:
    return World(MemoryUnitOfWorkFactory(), FixedClock(), PlainHasher(), DictTokens())


@pytest.fixture
def admin(world: World) -> User:
    return world.user(Role.ADMIN)


@pytest.fixture
def manager(world: World) -> User:
    return world.user(Role.MANAGER)


@pytest.fixture
def viewer(world: World) -> User:
    return world.user(Role.VIEWER)


def run[T](coroutine: Coroutine[Any, Any, T]) -> T:
    return asyncio.run(coroutine)


def add_channel(world: World, partner_id: str, handle: str) -> ChannelDTO:
    channel = Channel(
        id=ChannelId(new_id()),
        partner_id=PartnerId(partner_id),
        handle=Handle(handle),
        display_name="",
    )
    world.uow.state.channels[channel.id] = channel
    return ChannelDTO.from_entity(channel)
