from vinichannels.application.authorization import require
from vinichannels.application.dto import NotificationListDTO
from vinichannels.application.errors import NotFound
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.notifications.entities import Notification

MAX_LIMIT = 100


class ListNotifications:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(
        self, actor: User, limit: int = 30, unread_only: bool = False
    ) -> NotificationListDTO:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            items = await uow.notifications.list_recent(max(1, min(limit, MAX_LIMIT)), unread_only)
            return NotificationListDTO(items, await uow.notifications.count_unread())


class MarkNotificationRead:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, notification_id: str) -> Notification:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            item = await uow.notifications.get(notification_id)
            if item is None:
                raise NotFound("Không tìm thấy thông báo")
            item.mark_read(self._clock.now())
            await uow.notifications.save(item)
            await uow.commit()
            return item


class MarkAllNotificationsRead:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User) -> int:
        require(actor, Permission.ANALYTICS_READ)
        async with self._uow_factory() as uow:
            count = await uow.notifications.mark_all_read(self._clock.now())
            await uow.commit()
            return count
