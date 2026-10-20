from datetime import datetime, timedelta

import pytest

from vinichannels.domain.channels.entities import Channel, ChannelCredential
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode, Handle
from vinichannels.domain.shared.errors import InvalidStateError, ValidationError
from vinichannels.domain.shared.ids import ChannelId, PartnerId


def make_channel(
    display_name: str = "Brand A",
    connection_mode: ConnectionMode = ConnectionMode.PUBLIC,
    status: ChannelStatus = ChannelStatus.HEALTHY,
) -> Channel:
    return Channel(
        id=ChannelId("c1"),
        partner_id=PartnerId("p1"),
        handle=Handle("@brand.vn"),
        display_name=display_name,
        connection_mode=connection_mode,
        status=status,
    )


def test_blank_display_name_falls_back_to_handle() -> None:
    assert make_channel(display_name="  ").display_name == "@brand.vn"


def test_status_change_emits_event_only_when_different(now: datetime) -> None:
    channel = make_channel()
    assert channel.change_status(ChannelStatus.HEALTHY, now) is None
    event = channel.change_status(ChannelStatus.PROVIDER_ERROR, now)
    assert event is not None
    assert event.previous is ChannelStatus.HEALTHY
    assert event.current is ChannelStatus.PROVIDER_ERROR


def test_revoke_requires_authorized_mode(now: datetime) -> None:
    with pytest.raises(InvalidStateError):
        make_channel().revoke(now)
    channel = make_channel(connection_mode=ConnectionMode.AUTHORIZED)
    channel.revoke(now)
    assert channel.status is ChannelStatus.TOKEN_REVOKED
    assert not channel.is_syncable


def test_authorize_switches_mode_and_heals(now: datetime) -> None:
    channel = make_channel(status=ChannelStatus.TOKEN_REVOKED)
    channel.authorize(now)
    assert channel.connection_mode is ConnectionMode.AUTHORIZED
    assert channel.status is ChannelStatus.HEALTHY
    assert channel.is_syncable


def test_archive_deactivates_and_restore_reactivates(now: datetime) -> None:
    channel = make_channel()
    channel.archive(now)
    assert channel.is_archived
    assert not channel.is_active
    assert not channel.is_syncable
    with pytest.raises(InvalidStateError):
        channel.archive(now)
    channel.restore()
    assert channel.is_active
    assert channel.is_syncable


def test_credential_expiry_checks(now: datetime) -> None:
    credential = ChannelCredential(
        channel_id=ChannelId("c1"),
        access_token_enc=b"a",
        refresh_token_enc=b"r",
        expires_at=now + timedelta(days=2),
        refresh_expires_at=now + timedelta(days=30),
    )
    assert not credential.is_expired(now)
    assert credential.expires_within(now, timedelta(days=3))
    assert not credential.expires_within(now, timedelta(days=1))
    assert credential.can_refresh(now)
    assert not credential.can_refresh(now + timedelta(days=31))


def test_credential_requires_timezone_and_token(now: datetime) -> None:
    with pytest.raises(ValidationError):
        ChannelCredential(ChannelId("c1"), b"a", b"r", expires_at=datetime(2026, 1, 1))
    with pytest.raises(ValidationError):
        ChannelCredential(ChannelId("c1"), b"", b"r", expires_at=now)
