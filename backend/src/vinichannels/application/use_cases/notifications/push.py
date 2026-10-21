import asyncio
import logging
from collections.abc import Sequence

from vinichannels.application.authorization import require
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.push import PushMessage, PushSender, PushSubscriptionGone
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.notifications.entities import Notification, PushSubscription
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import new_id

_log = logging.getLogger(__name__)

MAX_INDIVIDUAL = 3
MAX_CONCURRENCY = 10


class GetPushConfig:
    def __init__(self, public_key: str | None) -> None:
        self._public_key = public_key

    def execute(self, actor: User) -> str | None:
        require(actor, Permission.ANALYTICS_READ)
        return self._public_key


class SubscribePush:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, endpoint: str, p256dh: str, auth: str) -> None:
        require(actor, Permission.ANALYTICS_READ)
        endpoint = endpoint.strip()
        if not endpoint.startswith("https://") or not p256dh.strip() or not auth.strip():
            raise ValidationError("Đăng ký thông báo đẩy không hợp lệ")
        async with self._uow_factory() as uow:
            await uow.push_subscriptions.upsert(
                PushSubscription(
                    new_id(), actor.id, endpoint, p256dh.strip(), auth.strip(), self._clock.now()
                )
            )
            await uow.commit()


class UnsubscribePush:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, actor: User, endpoint: str) -> None:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            await uow.push_subscriptions.remove(actor.id, endpoint.strip())
            await uow.commit()


def _url(item: Notification) -> str:
    return f"/channels/{item.channel_id}" if item.channel_id else "/channels"


def _messages(notifications: Sequence[Notification]) -> list[PushMessage]:
    if len(notifications) <= MAX_INDIVIDUAL:
        return [
            PushMessage(item.title, item.message, _url(item), item.id) for item in notifications
        ]
    titles = "; ".join(item.title for item in notifications[:MAX_INDIVIDUAL])
    return [
        PushMessage(
            f"{len(notifications)} thông báo mới",
            f"{titles}; và {len(notifications) - MAX_INDIVIDUAL} thông báo khác.",
            "/",
            "vini-summary",
        )
    ]


class PushNotifier:
    def __init__(self, uow_factory: UnitOfWorkFactory, sender: PushSender) -> None:
        self._uow_factory = uow_factory
        self._sender = sender

    async def notify(self, notifications: Sequence[Notification]) -> int:
        if not notifications:
            return 0
        async with self._uow_factory() as uow:
            subscriptions = await uow.push_subscriptions.list_all()
            users = {
                user_id: await uow.users.get(user_id)
                for user_id in {item.user_id for item in subscriptions}
            }
        targets = [
            item
            for item in subscriptions
            if (user := users.get(item.user_id)) is not None and user.can(Permission.ANALYTICS_READ)
        ]
        if not targets:
            return 0

        messages = _messages(notifications)
        gone: set[str] = set()
        gate = asyncio.Semaphore(MAX_CONCURRENCY)

        async def deliver(subscription: PushSubscription) -> int:
            delivered = 0
            for message in messages:
                async with gate:
                    try:
                        await self._sender.send(subscription, message)
                    except PushSubscriptionGone:
                        gone.add(subscription.endpoint)
                        return delivered
                    except Exception:
                        _log.exception("Gửi thông báo đẩy thất bại")
                        continue
                delivered += 1
            return delivered

        results = await asyncio.gather(*(deliver(item) for item in targets))
        if gone:
            async with self._uow_factory() as uow:
                await uow.push_subscriptions.remove_endpoints(sorted(gone))
                await uow.commit()
        return sum(results)
