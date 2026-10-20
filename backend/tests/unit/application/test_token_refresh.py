import json
from datetime import timedelta

from tests.unit.application.conftest import World, add_channel, run
from tests.unit.application.support import PlainCipher
from vinichannels.application.ports.data_provider import ProviderError
from vinichannels.application.ports.token_refresh import RefreshedToken, RefreshRequest
from vinichannels.application.use_cases.audit.query import ListAuditLog
from vinichannels.application.use_cases.partners.crud import CreatePartner
from vinichannels.application.use_cases.syncing.token_refresh import RefreshChannelTokens
from vinichannels.domain.audit.entities import AuditEntry
from vinichannels.domain.channels.entities import ChannelCredential
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode
from vinichannels.domain.identity.entities import User
from vinichannels.domain.syncing.policies import SyncErrorKind
from vinichannels.domain.syncing.providers import ProviderConfig, ProviderKey


class FakeRefresher:
    def __init__(self, result: RefreshedToken | Exception) -> None:
        self._result = result
        self.requests: list[RefreshRequest] = []

    async def refresh(self, request: RefreshRequest) -> RefreshedToken:
        self.requests.append(request)
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def _system_entries(world: World) -> list[AuditEntry]:
    return [entry for entry in world.uow.state.audit_entries if entry.actor_id == "system"]


def _fresh() -> RefreshedToken:
    return RefreshedToken(
        access_token="new-access",
        lifetime=timedelta(hours=24),
        refresh_token="new-refresh",
        refresh_lifetime=timedelta(days=365),
        scopes=frozenset({"user.info.basic"}),
    )


def _setup(
    world: World,
    manager: User,
    result: RefreshedToken | Exception,
    expires_in: timedelta = timedelta(hours=1),
    status: ChannelStatus = ChannelStatus.TOKEN_EXPIRING,
    refresh_token: str = "old-refresh",
) -> tuple[RefreshChannelTokens, FakeRefresher, str]:
    partner = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha"))
    channel_id = add_channel(world, partner.id, "alpha.vn").id
    channel = world.uow.state.channels[channel_id]
    channel.connection_mode = ConnectionMode.AUTHORIZED
    channel.status = status
    cipher = PlainCipher()
    world.uow.state.credentials[channel_id] = ChannelCredential(
        channel_id=channel.id,
        access_token_enc=cipher.encrypt("old-access"),
        refresh_token_enc=cipher.encrypt(refresh_token) if refresh_token else b"",
        expires_at=world.clock.now() + expires_in,
    )
    world.uow.state.providers[ProviderKey.TIKTOK.value] = ProviderConfig(
        key=ProviderKey.TIKTOK,
        enabled=True,
        credentials_enc=cipher.encrypt(json.dumps({"client_key": "ck", "client_secret": "cs"})),
    )
    refresher = FakeRefresher(result)
    return RefreshChannelTokens(world.uow, refresher, cipher, world.clock), refresher, channel_id


def test_successful_refresh_updates_token_and_restores_healthy(world: World, manager: User) -> None:
    refresh, refresher, channel_id = _setup(world, manager, _fresh())
    report = run(refresh.execute())
    assert (report.due, report.refreshed, report.revoked, report.failed) == (1, 1, 0, 0)
    assert refresher.requests == [RefreshRequest("old-refresh", "ck", "cs")]
    channel = world.uow.state.channels[channel_id]
    credential = world.uow.state.credentials[channel_id]
    cipher = PlainCipher()
    assert channel.status is ChannelStatus.HEALTHY
    assert cipher.decrypt(credential.access_token_enc) == "new-access"
    assert cipher.decrypt(credential.refresh_token_enc) == "new-refresh"
    assert credential.expires_at == world.clock.now() + timedelta(hours=24)
    assert credential.refresh_expires_at == world.clock.now() + timedelta(days=365)
    assert credential.scopes == {"user.info.basic"}
    assert _system_entries(world) == []


def test_revoked_refresh_marks_channel_and_writes_audit(world: World, manager: User) -> None:
    error = ProviderError(SyncErrorKind.TOKEN_REVOKED, "Refresh token không còn hiệu lực")
    refresh, _, channel_id = _setup(world, manager, error, status=ChannelStatus.HEALTHY)
    report = run(refresh.execute())
    assert (report.refreshed, report.revoked, report.failed) == (0, 1, 0)
    assert world.uow.state.channels[channel_id].status is ChannelStatus.TOKEN_REVOKED
    (entry,) = _system_entries(world)
    assert entry.action.value == "channel.token_revoked"
    assert entry.actor_id == "system"
    assert entry.target_id == channel_id
    assert "old-refresh" not in str(entry) and "old-access" not in str(entry)


def test_revoked_channel_is_not_refreshed_again(world: World, manager: User) -> None:
    error = ProviderError(SyncErrorKind.TOKEN_REVOKED, "Refresh token không còn hiệu lực")
    refresh, refresher, _ = _setup(world, manager, error)
    run(refresh.execute())
    assert run(refresh.execute()).due == 0
    assert len(refresher.requests) == 1


def test_transient_failure_keeps_channel_and_retries_next_run(world: World, manager: User) -> None:
    error = ProviderError(SyncErrorKind.SERVER_ERROR, "TikTok lỗi")
    refresh, refresher, channel_id = _setup(world, manager, error, status=ChannelStatus.HEALTHY)
    report = run(refresh.execute())
    assert (report.refreshed, report.revoked, report.failed) == (0, 0, 1)
    assert world.uow.state.channels[channel_id].status is ChannelStatus.HEALTHY
    assert _system_entries(world) == []
    run(refresh.execute())
    assert len(refresher.requests) == 2


def test_token_far_from_expiry_is_left_alone(world: World, manager: User) -> None:
    refresh, refresher, _ = _setup(world, manager, _fresh(), expires_in=timedelta(hours=20))
    report = run(refresh.execute())
    assert report.due == 0
    assert refresher.requests == []


def test_missing_refresh_token_revokes_only_once_access_token_expired(
    world: World, manager: User, admin: User
) -> None:
    refresh, refresher, channel_id = _setup(
        world, manager, _fresh(), refresh_token="", status=ChannelStatus.HEALTHY
    )
    assert run(refresh.execute()).skipped == 1
    world.clock.current += timedelta(hours=2)
    assert run(refresh.execute()).revoked == 1
    assert refresher.requests == []
    assert world.uow.state.channels[channel_id].status is ChannelStatus.TOKEN_REVOKED
    entries = run(ListAuditLog(world.uow).execute(admin, actor_id="system"))
    assert [entry.action.value for entry in entries] == ["channel.token_revoked"]
