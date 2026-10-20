from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.analytics.metrics import collect_period, metrics_for
from vinichannels.domain.analytics.periods import DateRange
from vinichannels.domain.channels.entities import Channel
from vinichannels.domain.notifications.entities import Notification, NotificationKind
from vinichannels.domain.notifications.rules import (
    ENGAGEMENT_PERIOD_DAYS,
    FAILURE_STREAK,
    engagement_dropped,
    failure_streak,
    token_expiring,
)
from vinichannels.domain.shared.ids import new_id

RUN_LOOKBACK = 20


class EvaluateAlerts:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self) -> int:
        now = self._clock.now()
        today = now.date()
        week = today.isocalendar()
        period = DateRange.last_days(ENGAGEMENT_PERIOD_DAYS, today)
        created = 0
        async with self._uow_factory() as uow:
            channels = [c for c in await uow.channels.list_all() if c.is_active]
            for channel in channels:
                candidates: list[tuple[NotificationKind, str, str, str]] = []

                runs = await uow.sync_runs.list_recent(RUN_LOOKBACK, channel_id=channel.id)
                streak, anchor = failure_streak(runs)
                if streak >= FAILURE_STREAK:
                    candidates.append(
                        (
                            NotificationKind.SYNC_FAILURES,
                            f"{NotificationKind.SYNC_FAILURES}:{channel.id}:{anchor or 'none'}",
                            f"Đồng bộ lỗi liên tiếp: {_name(channel)}",
                            f"{streak} lần đồng bộ gần nhất đều thất bại.",
                        )
                    )

                credential = await uow.credentials.get(channel.id)
                if credential is not None and token_expiring(credential, now):
                    stamp = credential.expires_at.isoformat()
                    candidates.append(
                        (
                            NotificationKind.TOKEN_EXPIRING,
                            f"{NotificationKind.TOKEN_EXPIRING}:{channel.id}:{stamp}",
                            f"Token sắp hết hạn: {_name(channel)}",
                            f"Token hết hạn lúc {credential.expires_at:%d/%m/%Y %H:%M}.",
                        )
                    )

                current = metrics_for(period, await collect_period(uow, channel.id, period))
                before = period.previous()
                previous = metrics_for(before, await collect_period(uow, channel.id, before))
                if engagement_dropped(current.erv, previous.erv):
                    assert current.erv is not None and previous.erv is not None
                    candidates.append(
                        (
                            NotificationKind.ENGAGEMENT_DROP,
                            f"{NotificationKind.ENGAGEMENT_DROP}:{channel.id}:{week.year}-W{week.week:02d}",
                            f"Tương tác giảm: {_name(channel)}",
                            f"Tỉ lệ tương tác {current.erv:.1%} so với {previous.erv:.1%} kỳ trước.",
                        )
                    )

                for kind, key, title, message in candidates:
                    if await uow.notifications.exists(key):
                        continue
                    await uow.notifications.add(
                        Notification(new_id(), kind, channel.id, key, title, message, now)
                    )
                    created += 1
            if created:
                await uow.commit()
        return created


def _name(channel: Channel) -> str:
    return channel.display_name or channel.handle.display
