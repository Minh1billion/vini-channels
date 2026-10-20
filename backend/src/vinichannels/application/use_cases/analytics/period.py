from collections.abc import Sequence

from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWork
from vinichannels.domain.analytics.periods import DateRange, PeriodSpec
from vinichannels.domain.shared.ids import ChannelId


async def resolve_period(
    uow: UnitOfWork,
    clock: Clock,
    spec: PeriodSpec,
    channel_ids: Sequence[ChannelId] | None = None,
) -> DateRange:
    earliest = await uow.snapshots.earliest_activity(channel_ids) if spec.all_time else None
    return spec.resolve(clock.now(), earliest)
