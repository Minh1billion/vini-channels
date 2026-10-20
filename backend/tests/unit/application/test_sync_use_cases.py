from datetime import timedelta

import pytest

from tests.unit.application.conftest import World, add_channel, run
from tests.unit.application.support import (
    FakeProvider,
    PlainCipher,
    creds,
    enable_apify,
    enable_provider,
    make_data,
    noop_sleep,
)
from vinichannels.application.errors import ChannelUnverified, Conflict, NotFound, PermissionDenied
from vinichannels.application.ports.data_provider import (
    ProviderError,
    ProviderUnavailable,
)
from vinichannels.application.use_cases.channels.register import (
    RegisterChannel,
    RegisterChannelCommand,
)
from vinichannels.application.use_cases.partners.crud import ArchivePartner, CreatePartner
from vinichannels.application.use_cases.syncing.providers import (
    ListProviders,
    SetChannelCredential,
    UpdateProvider,
    UpdateProviderCommand,
)
from vinichannels.application.use_cases.syncing.sync_channel import SyncChannel
from vinichannels.domain.channels.value_objects import ChannelStatus
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.partners.errors import PartnerArchived
from vinichannels.domain.shared.errors import InvalidStateError, ValidationError
from vinichannels.domain.shared.ids import ChannelId
from vinichannels.domain.syncing.entities import SyncStatus
from vinichannels.domain.syncing.policies import RetryPolicy, SyncErrorKind
from vinichannels.domain.syncing.providers import ProviderKey


def _setup(world: World, manager: User, *providers: FakeProvider) -> tuple[SyncChannel, str]:
    partner_id = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha")).id
    channel = add_channel(world, partner_id, "alpha.vn")
    mapping = {provider.key: provider for provider in providers}
    sync = SyncChannel(
        world.uow,
        mapping,
        PlainCipher(),
        world.clock,
        RetryPolicy(max_attempts=2),
        noop_sleep,
    )
    return sync, channel.id


def test_sync_stores_snapshots_and_updates_channel(world: World, manager: User) -> None:
    provider = FakeProvider(ProviderKey.APIFY.value, make_data(world))
    sync, channel_id = _setup(world, manager, provider)
    enable_apify(world)
    result = run(sync.execute(manager, channel_id))
    assert result.status is SyncStatus.SUCCESS
    assert (result.source, result.items_fetched) == ("apify", 2)
    state = world.uow.state
    assert len(state.videos) == 2
    assert len(state.video_snapshots) == 2
    assert state.channel_snapshots[0].followers == 1200
    channel = state.channels[channel_id]
    assert channel.avatar_url == "http://a/avatar.png"
    assert channel.display_name == "Alpha Shop"
    assert channel.platform_channel_id == "pid"

    world.clock.current += timedelta(hours=6)
    run(sync.execute(manager, channel_id))
    assert len(state.videos) == 2
    assert len(state.video_snapshots) == 4
    assert len(state.channel_snapshots) == 2


def test_falls_back_to_next_provider_and_uses_retry(world: World, manager: User) -> None:
    flaky = FakeProvider(
        ProviderKey.SCRAPECREATORS.value, ProviderError(SyncErrorKind.SERVER_ERROR, "boom")
    )
    backup = FakeProvider(ProviderKey.APIFY.value, make_data(world))
    sync, channel_id = _setup(world, manager, flaky, backup)
    enable_provider(world, ProviderKey.SCRAPECREATORS, 10, credentials_enc=creds("k"))
    enable_apify(world, 20)
    result = run(sync.execute(manager, channel_id))
    assert result.status is SyncStatus.SUCCESS
    assert result.source == "apify"
    assert len(flaky.requests) == 2
    assert flaky.requests[0].credentials == {"api_key": "k"}


def test_provider_unavailable_skips_without_retry(world: World, manager: User) -> None:
    broken = FakeProvider(ProviderKey.SCRAPECREATORS.value, ProviderUnavailable("hết credit"))
    backup = FakeProvider(ProviderKey.APIFY.value, make_data(world))
    sync, channel_id = _setup(world, manager, broken, backup)
    enable_provider(world, ProviderKey.SCRAPECREATORS, 10, credentials_enc=creds("k"))
    enable_apify(world, 20)
    assert run(sync.execute(manager, channel_id)).source == "apify"
    assert len(broken.requests) == 1


def test_terminal_error_sets_channel_status_and_stops(world: World, manager: User) -> None:
    first = FakeProvider(
        ProviderKey.SCRAPECREATORS.value, ProviderError(SyncErrorKind.NOT_FOUND, "x")
    )
    second = FakeProvider(ProviderKey.APIFY.value, make_data(world))
    sync, channel_id = _setup(world, manager, first, second)
    enable_provider(world, ProviderKey.SCRAPECREATORS, 10, credentials_enc=creds("k"))
    enable_apify(world, 20)
    result = run(sync.execute(manager, channel_id))
    assert result.status is SyncStatus.FAILED
    assert result.error_code == "not_found"
    assert world.uow.state.channels[channel_id].status is ChannelStatus.NOT_FOUND
    assert second.requests == []
    with pytest.raises(InvalidStateError):
        run(sync.execute(manager, channel_id))


def test_all_transient_failures_mark_provider_error_then_recover(
    world: World, manager: User
) -> None:
    down = ProviderError(SyncErrorKind.NETWORK, "down")
    provider = FakeProvider(ProviderKey.APIFY.value, down, down, make_data(world))
    sync, channel_id = _setup(world, manager, provider)
    enable_apify(world)
    failed = run(sync.execute(manager, channel_id))
    assert failed.status is SyncStatus.FAILED
    assert world.uow.state.channels[channel_id].status is ChannelStatus.PROVIDER_ERROR
    world.clock.current += timedelta(minutes=1)
    assert run(sync.execute(manager, channel_id)).status is SyncStatus.SUCCESS
    assert world.uow.state.channels[channel_id].status is ChannelStatus.HEALTHY


def test_partial_when_provider_returns_warning(world: World, manager: User) -> None:
    provider = FakeProvider(ProviderKey.APIFY.value, make_data(world, warning="thiếu video"))
    sync, channel_id = _setup(world, manager, provider)
    enable_apify(world)
    result = run(sync.execute(manager, channel_id))
    assert result.status is SyncStatus.PARTIAL
    assert result.error_message == "thiếu video"


def test_quota_and_missing_providers(world: World, manager: User) -> None:
    provider = FakeProvider(ProviderKey.SCRAPECREATORS.value, make_data(world))
    sync, channel_id = _setup(world, manager, provider)
    with pytest.raises(Conflict):
        run(sync.execute(manager, channel_id))
    enable_provider(world, ProviderKey.SCRAPECREATORS, credentials_enc=creds("k"), monthly_quota=1)
    run(sync.execute(manager, channel_id))
    with pytest.raises(Conflict):
        run(sync.execute(manager, channel_id))


def test_tiktok_needs_authorized_channel_with_valid_token(world: World, manager: User) -> None:
    admin = world.user(Role.ADMIN)
    tiktok = FakeProvider(ProviderKey.TIKTOK.value, make_data(world))
    sync, channel_id = _setup(world, manager, tiktok)
    enable_provider(world, ProviderKey.TIKTOK)
    with pytest.raises(Conflict):
        run(sync.execute(manager, channel_id))
    set_credential = SetChannelCredential(world.uow, PlainCipher(), world.clock)
    expires = world.clock.now() + timedelta(days=1)
    run(set_credential.execute(admin, channel_id, " tok ", expires))
    assert run(sync.execute(manager, channel_id)).source == "tiktok"
    assert tiktok.requests[0].credentials == {"access_token": "tok"}
    expired = world.clock.now() - timedelta(minutes=1)
    run(set_credential.execute(admin, channel_id, "tok", expired))
    with pytest.raises(Conflict):
        run(sync.execute(manager, channel_id))


def test_sync_requires_permission(world: World, manager: User, viewer: User) -> None:
    sync, channel_id = _setup(
        world, manager, FakeProvider(ProviderKey.APIFY.value, make_data(world))
    )
    with pytest.raises(PermissionDenied):
        run(sync.execute(viewer, channel_id))
    with pytest.raises(NotFound):
        run(sync.execute(manager, ChannelId("missing")))


def test_provider_settings_validation_and_secrets(world: World, manager: User) -> None:
    admin = world.user(Role.ADMIN)
    available = [ProviderKey.SCRAPECREATORS, ProviderKey.APIFY]
    update = UpdateProvider(world.uow, PlainCipher(), world.clock, available)
    listing = ListProviders(world.uow, world.clock, available)

    names = [item.key for item in run(listing.execute(manager))]
    assert names == ["scrapecreators", "apify"]
    with pytest.raises(PermissionDenied):
        run(update.execute(manager, UpdateProviderCommand("apify", enabled=False)))
    with pytest.raises(NotFound):
        run(update.execute(admin, UpdateProviderCommand("tiktok")))
    with pytest.raises(ValidationError):
        run(update.execute(admin, UpdateProviderCommand("scrapecreators", enabled=True)))
    with pytest.raises(ValidationError):
        run(update.execute(admin, UpdateProviderCommand("scrapecreators", credentials={"x": "1"})))
    with pytest.raises(ValidationError):
        run(update.execute(admin, UpdateProviderCommand("apify", credentials={"actor_id": "a/b"})))

    dto = run(
        update.execute(
            admin,
            UpdateProviderCommand(
                "scrapecreators", enabled=True, priority=5, credentials={"api_key": " k "}
            ),
        )
    )
    assert (dto.enabled, dto.priority, dto.is_configured) == (True, 5, True)
    assert not hasattr(dto, "credentials")
    stored = world.uow.state.providers["scrapecreators"].credentials_enc
    assert stored is not None
    assert b"k" in stored
    assert run(listing.execute(manager))[0].key == "scrapecreators"

    cleared = run(
        update.execute(
            admin, UpdateProviderCommand("scrapecreators", enabled=False, credentials={})
        )
    )
    assert cleared.is_configured is False


def _register(world: World, *providers: FakeProvider) -> RegisterChannel:
    return RegisterChannel(
        world.uow,
        {provider.key: provider for provider in providers},
        PlainCipher(),
        world.clock,
        RetryPolicy(max_attempts=2),
        noop_sleep,
    )


def test_register_channel_saves_channel_and_first_run_when_crawl_works(
    world: World, manager: User
) -> None:
    partner_id = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha")).id
    enable_apify(world)
    register = _register(world, FakeProvider(ProviderKey.APIFY.value, make_data(world)))
    created = run(
        register.execute(manager, RegisterChannelCommand(partner_id, "@Alpha.VN", "apify"))
    )
    state = world.uow.state
    assert created.handle == "alpha.vn"
    assert created.display_name == "Alpha Shop"
    assert len(state.videos) == 2
    runs = list(state.sync_runs.values())
    assert [(item.status, item.source) for item in runs] == [(SyncStatus.SUCCESS, "apify")]


def test_register_channel_saves_nothing_when_crawl_fails(world: World, manager: User) -> None:
    partner_id = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha")).id
    enable_apify(world)
    failing = FakeProvider(ProviderKey.APIFY.value, ProviderError(SyncErrorKind.NOT_FOUND, "x"))
    with pytest.raises(ChannelUnverified):
        command = RegisterChannelCommand(partner_id, "a.vn", "apify")
        run(_register(world, failing).execute(manager, command))
    assert world.uow.state.channels == {}
    assert world.uow.state.sync_runs == {}


def test_register_channel_validates_input(world: World, manager: User) -> None:
    partner_id = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha")).id
    enable_apify(world)
    register = _register(world, FakeProvider(ProviderKey.APIFY.value, make_data(world)))

    def attempt(**fields: object) -> object:
        values = {"partner_id": partner_id, "handle": "alpha.vn", "provider": "apify", **fields}
        return run(register.execute(manager, RegisterChannelCommand(**values)))  # type: ignore[arg-type]

    attempt(sync_cron="0 */6 * * *")
    with pytest.raises(Conflict):
        attempt()
    with pytest.raises(ValidationError):
        attempt(handle="!!")
    with pytest.raises(ValidationError):
        attempt(handle="other", sync_cron="not cron")
    with pytest.raises(ValidationError):
        attempt(handle="other", timezone="Mars/Base")
    with pytest.raises(ValidationError):
        attempt(handle="other", provider="nope")
    with pytest.raises(NotFound):
        attempt(handle="other", partner_id="missing")
    world.uow.state.providers["apify"].enabled = False
    with pytest.raises(Conflict):
        attempt(handle="other")
    run(ArchivePartner(world.uow, world.clock).execute(manager, partner_id))
    with pytest.raises(PartnerArchived):
        attempt(handle="other")
    assert len(world.uow.state.channels) == 1
