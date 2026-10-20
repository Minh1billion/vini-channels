from datetime import UTC, date, datetime, time, timedelta

from vinichannels.application.authorization import require
from vinichannels.application.dto import AuditEntryDTO
from vinichannels.application.ports.repositories import AuditFilter
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.errors import ValidationError

MAX_LIMIT = 500


def _start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


class ListAuditLog:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(
        self,
        actor: User,
        actor_id: str | None = None,
        action: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntryDTO]:
        require(actor, Permission.AUDIT_READ)
        if date_from and date_to and date_from > date_to:
            raise ValidationError("Khoảng ngày không hợp lệ")
        try:
            parsed = AuditAction(action) if action else None
        except ValueError as error:
            raise ValidationError("Loại thao tác không hợp lệ") from error
        criteria = AuditFilter(
            actor_id=actor_id,
            action=parsed,
            since=_start(date_from) if date_from else None,
            until=_start(date_to + timedelta(days=1)) if date_to else None,
        )
        async with self._uow_factory() as uow:
            entries = await uow.audit.search(
                criteria, min(max(limit, 1), MAX_LIMIT), max(offset, 0)
            )
        return [AuditEntryDTO.from_entity(entry) for entry in entries]
