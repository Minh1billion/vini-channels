import asyncio
from datetime import timedelta

import pytest

from tests.unit.application.conftest import World, add_channel, run
from tests.unit.application.test_analytics_use_cases import at, seed_video
from vinichannels.application.errors import NotFound, PermissionDenied
from vinichannels.application.ports.push import PushMessage, PushSubscriptionGone
from vinichannels.application.use_cases.jobs.fetch_jobs import (
    FetchJobs,
    JobOutcome,
    JobStatus,
)
from vinichannels.application.use_cases.notifications.alerts import EvaluateAlerts
from vinichannels.application.use_cases.notifications.inbox import (
    ListNotifications,
    MarkAllNotificationsRead,
    MarkNotificationRead,
)
from vinichannels.application.use_cases.notifications.job_alerts import JobFinishedNotifier
from vinichannels.application.use_cases.notifications.push import (
    PushNotifier,
    SubscribePush,
    UnsubscribePush,
)
from vinichannels.application.use_cases.partners.crud import CreatePartner
from vinichannels.domain.channels.entities import ChannelCredential
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.notifications.entities import NotificationKind, PushSubscription
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import ChannelId, SyncRunId, new_id
from vinichannels.domain.syncing.entities import SyncRun, SyncStatus, SyncTrigger


def _run(world: World, channel_id: str, hour: int, status: SyncStatus) -> None:
    item = SyncRun(
        SyncRunId(new_id()),
        ChannelId(channel_id),
        at(18, hour),
        SyncTrigger.SCHEDULED,
        at(18, hour),
    )
    item.status = status
    world.uow.state.sync_runs[item.id] = item


@pytest.fixture
def channels(world: World, manager: User) -> dict[str, str]:
    partner = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha"))
    ids = {
        name: add_channel(world, partner.id, name).id
        for name in ("failing", "token", "drop", "calm")
    }
    for hour in (1, 2, 3):
        _run(world, ids["failing"], hour, SyncStatus.FAILED)
    _run(world, ids["calm"], 1, SyncStatus.FAILED)
    _run(world, ids["calm"], 2, SyncStatus.FAILED)
    world.uow.state.credentials[ids["token"]] = ChannelCredential(
        ChannelId(ids["token"]), b"a", b"r", world.clock.now() + timedelta(days=1)
    )
    seed_video(world, ids["drop"], "old", at(8), (at(10), 1000, 100))
    seed_video(world, ids["drop"], "new", at(14), (at(18), 1000, 50))
    seed_video(world, ids["calm"], "calm-old", at(8), (at(10), 1000, 100))
    seed_video(world, ids["calm"], "calm-new", at(14), (at(18), 1000, 95))
    return ids


def test_each_rule_creates_exactly_one_notification(world: World, channels: dict[str, str]) -> None:
    assert run(EvaluateAlerts(world.uow, world.clock).execute()) == 3

    items = list(world.uow.state.notifications.values())
    by_kind = {item.kind: item for item in items}
    assert len(items) == 3
    assert by_kind[NotificationKind.SYNC_FAILURES].channel_id == channels["failing"]
    assert by_kind[NotificationKind.TOKEN_EXPIRING].channel_id == channels["token"]
    assert by_kind[NotificationKind.ENGAGEMENT_DROP].channel_id == channels["drop"]


def test_repeated_evaluation_does_not_duplicate(world: World, channels: dict[str, str]) -> None:
    evaluate = EvaluateAlerts(world.uow, world.clock)

    assert run(evaluate.execute()) == 3
    assert run(evaluate.execute()) == 0
    assert len(world.uow.state.notifications) == 3


def test_new_failure_streak_after_success_notifies_again(
    world: World, channels: dict[str, str]
) -> None:
    evaluate = EvaluateAlerts(world.uow, world.clock)
    run(evaluate.execute())
    _run(world, channels["failing"], 4, SyncStatus.SUCCESS)
    for hour in (5, 6, 7):
        _run(world, channels["failing"], hour, SyncStatus.FAILED)

    assert run(evaluate.execute()) == 1


def test_inbox_lists_and_marks_read(world: World, manager: User, channels: dict[str, str]) -> None:
    run(EvaluateAlerts(world.uow, world.clock).execute())
    listing = run(ListNotifications(world.uow).execute(manager))
    assert (len(listing.items), listing.unread_count) == (3, 3)

    first = run(MarkNotificationRead(world.uow, world.clock).execute(manager, listing.items[0].id))
    assert first.is_read
    assert run(ListNotifications(world.uow).execute(manager, unread_only=True)).unread_count == 2

    assert run(MarkAllNotificationsRead(world.uow, world.clock).execute(manager)) == 2
    assert run(ListNotifications(world.uow).execute(manager)).unread_count == 0
    with pytest.raises(NotFound):
        run(MarkNotificationRead(world.uow, world.clock).execute(manager, "missing"))


class RecordingSender:
    def __init__(self, gone: set[str] | None = None) -> None:
        self.sent: list[tuple[str, PushMessage]] = []
        self._gone = gone or set()

    async def send(self, subscription: PushSubscription, message: PushMessage) -> None:
        if subscription.endpoint in self._gone:
            raise PushSubscriptionGone(subscription.endpoint)
        self.sent.append((subscription.endpoint, message))


def test_push_subscription_requires_permission_and_https(world: World, manager: User) -> None:
    subscribe = SubscribePush(world.uow, world.clock)
    run(subscribe.execute(manager, "https://push.example/a", "key", "auth"))
    run(subscribe.execute(manager, "https://push.example/a", "key2", "auth2"))
    assert len(world.uow.state.push_subscriptions) == 1
    with pytest.raises(ValidationError):
        run(subscribe.execute(manager, "http://push.example/b", "key", "auth"))
    inactive = world.user(Role.VIEWER)
    inactive.deactivate()
    with pytest.raises(PermissionDenied):
        run(subscribe.execute(inactive, "https://push.example/c", "key", "auth"))

    run(UnsubscribePush(world.uow).execute(manager, "https://push.example/a"))
    assert not world.uow.state.push_subscriptions


def test_alerts_push_to_subscribers_and_drop_gone_endpoints(
    world: World, manager: User, channels: dict[str, str]
) -> None:
    subscribe = SubscribePush(world.uow, world.clock)
    run(subscribe.execute(manager, "https://push.example/live", "key", "auth"))
    run(subscribe.execute(manager, "https://push.example/dead", "key", "auth"))
    sender = RecordingSender(gone={"https://push.example/dead"})
    evaluate = EvaluateAlerts(world.uow, world.clock, PushNotifier(world.uow, sender))

    assert run(evaluate.execute()) == 3

    assert {endpoint for endpoint, _ in sender.sent} == {"https://push.example/live"}
    assert len(sender.sent) == 3
    assert set(world.uow.state.push_subscriptions) == {"https://push.example/live"}
    assert run(evaluate.execute()) == 0
    assert len(sender.sent) == 3


def test_many_notifications_collapse_into_one_push(world: World, manager: User) -> None:
    run(SubscribePush(world.uow, world.clock).execute(manager, "https://push.example/a", "k", "a"))
    partner = run(CreatePartner(world.uow, world.clock).execute(manager, "Beta"))
    for index in range(5):
        channel = add_channel(world, partner.id, f"flaky{index}")
        for hour in (1, 2, 3):
            _run(world, channel.id, hour, SyncStatus.FAILED)
    sender = RecordingSender()

    run(EvaluateAlerts(world.uow, world.clock, PushNotifier(world.uow, sender)).execute())

    assert len(sender.sent) == 1
    assert sender.sent[0][1].title == "5 thông báo mới"


def test_finished_jobs_create_notifications_and_push(world: World, manager: User) -> None:
    run(SubscribePush(world.uow, world.clock).execute(manager, "https://push.example/a", "k", "a"))
    sender = RecordingSender()
    notifier = JobFinishedNotifier(world.uow, world.clock, PushNotifier(world.uow, sender))
    jobs = FetchJobs(world.clock, on_finish=notifier.notify)

    async def scenario() -> None:
        async def ok(_: object) -> JobOutcome:
            return JobOutcome(JobStatus.SUCCESS, "2 video", "chan1")

        async def boom(_: object) -> JobOutcome:
            return JobOutcome(JobStatus.FAILED, "Hết hạn mức")

        jobs.launch("sync", "@good", "chan1", ok)
        jobs.launch("register", "@bad", None, boom)
        await asyncio.gather(*list(jobs._tasks))

    run(scenario())

    items = {item.kind: item for item in world.uow.state.notifications.values()}
    assert items[NotificationKind.JOB_SUCCEEDED].channel_id == "chan1"
    assert items[NotificationKind.JOB_FAILED].channel_id == ""
    assert {message.url for _, message in sender.sent} == {"/channels/chan1", "/channels"}
