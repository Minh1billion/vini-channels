from dataclasses import dataclass

from vinichannels.application.authorization import require
from vinichannels.application.dto import UNSET, ChannelDTO, Maybe, Unset
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.audit.recording import change, record
from vinichannels.application.use_cases.channels.common import (
    load_active_partner,
    load_channel,
    validate_schedule,
)
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.ids import PartnerId


@dataclass(frozen=True, slots=True)
class UpdateChannelCommand:
    channel_id: str
    display_name: Maybe[str] = UNSET
    avatar_url: Maybe[str | None] = UNSET
    is_active: Maybe[bool] = UNSET


class UpdateChannel:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, command: UpdateChannelCommand) -> ChannelDTO:
        require(actor, Permission.PARTNERS_WRITE)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, command.channel_id)
            changes: dict[str, str] = {}
            if not isinstance(command.display_name, Unset):
                previous_name = channel.display_name
                channel.display_name = command.display_name.strip() or channel.handle.display
                if channel.display_name != previous_name:
                    changes["display_name"] = change(previous_name, channel.display_name)
            if not isinstance(command.avatar_url, Unset):
                if command.avatar_url != channel.avatar_url:
                    changes["avatar_url"] = "changed"
                channel.avatar_url = command.avatar_url
            if not isinstance(command.is_active, Unset) and not channel.is_archived:
                if command.is_active != channel.is_active:
                    changes["is_active"] = change(channel.is_active, command.is_active)
                channel.is_active = command.is_active
            await uow.channels.save(channel)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.CHANNEL_UPDATE,
                "channel",
                channel.id,
                channel.handle.display,
                changes,
            )
            await uow.commit()
        return ChannelDTO.from_entity(channel)


class SetChannelSchedule:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(
        self, actor: User, channel_id: str, cron: str | None, timezone: str
    ) -> ChannelDTO:
        require(actor, Permission.SYNC_WRITE)
        validate_schedule(cron, timezone)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            before = f"{channel.sync_cron or 'mặc định'} ({channel.timezone})"
            channel.set_schedule(cron, timezone)
            await uow.channels.save(channel)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.CHANNEL_SCHEDULE,
                "channel",
                channel.id,
                channel.handle.display,
                {"schedule": change(before, f"{channel.sync_cron or 'mặc định'} ({timezone})")},
            )
            await uow.commit()
        return ChannelDTO.from_entity(channel)


class ArchiveChannel:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, channel_id: str) -> ChannelDTO:
        require(actor, Permission.PARTNERS_WRITE)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            channel.archive(self._clock.now())
            await uow.channels.save(channel)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.CHANNEL_ARCHIVE,
                "channel",
                channel.id,
                channel.handle.display,
            )
            await uow.commit()
        return ChannelDTO.from_entity(channel)


class RestoreChannel:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, channel_id: str) -> ChannelDTO:
        require(actor, Permission.PARTNERS_WRITE)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
            await load_active_partner(uow, channel.partner_id)
            channel.restore()
            await uow.channels.save(channel)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.CHANNEL_RESTORE,
                "channel",
                channel.id,
                channel.handle.display,
            )
            await uow.commit()
        return ChannelDTO.from_entity(channel)


class GetChannel:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, actor: User, channel_id: str) -> ChannelDTO:
        require(actor, Permission.PARTNERS_READ)
        async with self._uow_factory() as uow:
            channel = await load_channel(uow, channel_id)
        return ChannelDTO.from_entity(channel)


class ListChannels:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(
        self,
        actor: User,
        partner_id: str | None = None,
        include_archived: bool = False,
        search: str | None = None,
    ) -> list[ChannelDTO]:
        require(actor, Permission.PARTNERS_READ)
        async with self._uow_factory() as uow:
            channels = await uow.channels.list_all(
                PartnerId(partner_id) if partner_id else None, include_archived, search
            )
        return [ChannelDTO.from_entity(channel) for channel in channels]
