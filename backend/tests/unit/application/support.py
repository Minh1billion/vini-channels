from datetime import timedelta

from tests.unit.application.conftest import World
from vinichannels.application.ports.data_provider import (
    FetchedProfile,
    FetchedVideo,
    FetchRequest,
    ProviderData,
)
from vinichannels.domain.syncing.providers import ProviderConfig, ProviderKey


class PlainCipher:
    def encrypt(self, text: str) -> bytes:
        return f"enc:{text}".encode()

    def decrypt(self, data: bytes) -> str:
        return data.decode().removeprefix("enc:")


class FakeProvider:
    def __init__(self, key: str, *results: ProviderData | Exception) -> None:
        self.key = key
        self._results = list(results)
        self.requests: list[FetchRequest] = []

    async def fetch(self, request: FetchRequest) -> ProviderData:
        self.requests.append(request)
        result = self._results.pop(0) if len(self._results) > 1 else self._results[0]
        if isinstance(result, Exception):
            raise result
        return result


def make_data(world: World, views: int = 100, warning: str | None = None) -> ProviderData:
    return ProviderData(
        profile=FetchedProfile("pid", "Alpha Shop", "http://a/avatar.png", 1200, 5, 900, 3),
        videos=(
            FetchedVideo("v1", world.clock.now() - timedelta(days=1), views, 10, 2, 1, 4),
            FetchedVideo("v2", world.clock.now() - timedelta(days=2), views * 2, 20, 3, 2),
        ),
        warning=warning,
    )


async def noop_sleep(_: float) -> None:
    return None


def enable_provider(world: World, key: ProviderKey, priority: int = 10, **fields: object) -> None:
    world.uow.state.providers[key.value] = ProviderConfig(
        key=key,
        enabled=True,
        priority=priority,
        **fields,  # type: ignore[arg-type]
    )


def creds(secret: str, field: str = "api_key") -> bytes:
    return PlainCipher().encrypt(f'{{"{field}": "{secret}"}}')


def enable_apify(world: World, priority: int = 10) -> None:
    enable_provider(world, ProviderKey.APIFY, priority, credentials_enc=creds("t", "api_token"))
