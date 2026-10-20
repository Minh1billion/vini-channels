import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

from vinichannels.application.dto import SyncRunDTO
from vinichannels.application.errors import Conflict, NotFound
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.notifications.alerts import EvaluateAlerts
from vinichannels.application.use_cases.syncing.sync_channel import SyncChannel
from vinichannels.application.use_cases.syncing.token_refresh import (
    RefreshChannelTokens,
    TokenRefreshReport,
)
from vinichannels.domain.shared.errors import InvalidStateError, ValidationError
from vinichannels.domain.shared.ids import ChannelId
from vinichannels.domain.syncing.entities import SyncStatus, SyncTrigger
from vinichannels.domain.syncing.schedule import SchedulePreset, SyncSchedule

_log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DueSyncReport:
    due: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    invalid_schedules: int = 0
    tokens_refreshed: int = 0
    tokens_revoked: int = 0
    token_failures: int = 0


class RunDueSyncs:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        sync_channel: SyncChannel,
        clock: Clock,
        max_concurrency: int = 3,
        max_batch: int = 100,
        token_refresh: RefreshChannelTokens | None = None,
        alerts: EvaluateAlerts | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._sync = sync_channel
        self._clock = clock
        self._max_concurrency = max(1, max_concurrency)
        self._max_batch = max(1, max_batch)
        self._token_refresh = token_refresh
        self._alerts = alerts

    async def _refresh_tokens(self) -> TokenRefreshReport:
        if self._token_refresh is None:
            return TokenRefreshReport()
        try:
            return await self._token_refresh.execute()
        except Exception:
            _log.exception("Làm mới token theo lịch thất bại")
            return TokenRefreshReport()

    async def _evaluate_alerts(self) -> None:
        if self._alerts is None:
            return
        try:
            await self._alerts.execute()
        except Exception:
            _log.exception("Đánh giá cảnh báo thất bại")

    async def execute(self) -> DueSyncReport:
        report = await self._sync_due()
        await self._evaluate_alerts()
        return report

    async def _sync_due(self) -> DueSyncReport:
        tokens = await self._refresh_tokens()
        now = self._clock.now()
        async with self._uow_factory() as uow:
            channels = await uow.channels.list_all()
            last_slots = await uow.sync_runs.latest_slots()
        due: list[tuple[ChannelId, datetime]] = []
        invalid = 0
        for channel in channels:
            if not channel.is_syncable:
                continue
            try:
                schedule = SyncSchedule.from_cron(
                    channel.sync_cron or SchedulePreset.DAILY.value, channel.timezone
                )
                slot = schedule.pending_slot(last_slots.get(channel.id), now)
            except ValidationError:
                invalid += 1
                continue
            if slot is not None:
                due.append((channel.id, slot))
        due.sort(key=lambda item: item[1])
        batch = due[: self._max_batch]
        gate = asyncio.Semaphore(self._max_concurrency)

        async def run_one(channel_id: ChannelId, slot: datetime) -> SyncRunDTO | None:
            async with gate:
                try:
                    return await self._sync.run(channel_id, SyncTrigger.SCHEDULED, slot)
                except (Conflict, InvalidStateError, NotFound):
                    return None

        outcomes = await asyncio.gather(
            *(run_one(channel_id, slot) for channel_id, slot in batch),
            return_exceptions=True,
        )
        succeeded = failed = skipped = 0
        for outcome in outcomes:
            if isinstance(outcome, BaseException):
                failed += 1
                _log.error("Đồng bộ theo lịch gặp lỗi không lường trước", exc_info=outcome)
            elif outcome is None:
                skipped += 1
            elif outcome.status is SyncStatus.FAILED:
                failed += 1
            else:
                succeeded += 1
        return DueSyncReport(
            due=len(due),
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            invalid_schedules=invalid,
            tokens_refreshed=tokens.refreshed,
            tokens_revoked=tokens.revoked,
            token_failures=tokens.failed,
        )
