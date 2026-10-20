from datetime import UTC, datetime

from vinichannels.application.authorization import require
from vinichannels.application.dto import SyncRunDTO, SyncScheduleDTO
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.ids import ChannelId
from vinichannels.domain.syncing.entities import SyncStatus
from vinichannels.domain.syncing.schedule import SchedulePreset, SyncSchedule

MAX_RUNS = 200
_FAR_FUTURE = datetime.max.replace(tzinfo=UTC)


class ListSyncRuns:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(
        self,
        actor: User,
        limit: int = 50,
        status: SyncStatus | None = None,
        channel_id: str | None = None,
    ) -> list[SyncRunDTO]:
        require(actor, Permission.SYNC_READ)
        capped = max(1, min(limit, MAX_RUNS))
        handles: dict[str, str] = {}
        result: list[SyncRunDTO] = []
        async with self._uow_factory() as uow:
            for run in await uow.sync_runs.list_recent(
                capped, status, ChannelId(channel_id) if channel_id else None
            ):
                if run.channel_id not in handles:
                    channel = await uow.channels.get(ChannelId(run.channel_id))
                    handles[run.channel_id] = channel.handle.value if channel else "?"
                result.append(SyncRunDTO.from_entity(run, handles[run.channel_id]))
        return result


class ListSyncSchedules:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User) -> list[SyncScheduleDTO]:
        require(actor, Permission.SYNC_READ)
        now = self._clock.now()
        async with self._uow_factory() as uow:
            channels = await uow.channels.list_all()
        items: list[SyncScheduleDTO] = []
        for channel in channels:
            cron = channel.sync_cron or SchedulePreset.DAILY.value
            next_run = (
                SyncSchedule.from_cron(cron, channel.timezone).next_run_after(now)
                if channel.is_active
                else None
            )
            items.append(
                SyncScheduleDTO(
                    channel_id=channel.id,
                    handle=channel.handle.value,
                    display_name=channel.display_name,
                    connection_mode=channel.connection_mode,
                    status=channel.status,
                    is_active=channel.is_active,
                    cron=cron,
                    is_default_cron=channel.sync_cron is None,
                    timezone=channel.timezone,
                    next_run_at=next_run,
                )
            )
        return sorted(items, key=lambda item: (item.next_run_at or _FAR_FUTURE, item.handle))
