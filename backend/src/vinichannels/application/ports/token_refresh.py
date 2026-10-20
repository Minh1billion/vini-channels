from dataclasses import dataclass, field
from datetime import timedelta
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RefreshRequest:
    refresh_token: str
    client_key: str
    client_secret: str


@dataclass(frozen=True, slots=True)
class RefreshedToken:
    access_token: str
    lifetime: timedelta
    refresh_token: str | None = None
    refresh_lifetime: timedelta | None = None
    scopes: frozenset[str] = field(default_factory=frozenset)


class TokenRefresher(Protocol):
    async def refresh(self, request: RefreshRequest) -> RefreshedToken: ...
