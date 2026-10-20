from collections.abc import Sequence
from datetime import datetime, timedelta

from vinichannels.domain.analytics.metrics import change_ratio
from vinichannels.domain.channels.entities import ChannelCredential
from vinichannels.domain.syncing.entities import SyncRun, SyncStatus

FAILURE_STREAK = 3
TOKEN_WINDOW = timedelta(days=3)
ENGAGEMENT_DROP_RATIO = 0.2
ENGAGEMENT_PERIOD_DAYS = 7


def failure_streak(runs_newest_first: Sequence[SyncRun]) -> tuple[int, str | None]:
    streak = 0
    for run in runs_newest_first:
        if run.status is SyncStatus.RUNNING:
            continue
        if run.status is not SyncStatus.FAILED:
            return streak, run.id
        streak += 1
    return streak, None


def token_expiring(credential: ChannelCredential, now: datetime) -> bool:
    return credential.expires_within(now, TOKEN_WINDOW)


def engagement_dropped(current: float | None, previous: float | None) -> bool:
    ratio = change_ratio(current, previous)
    return ratio is not None and ratio <= -ENGAGEMENT_DROP_RATIO
