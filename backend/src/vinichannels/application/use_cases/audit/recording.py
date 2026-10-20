from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWork
from vinichannels.domain.audit.entities import AuditAction, AuditEntry
from vinichannels.domain.identity.entities import User
from vinichannels.domain.shared.ids import new_id

SYSTEM_ACTOR_ID = "system"
SYSTEM_ACTOR_LABEL = "Hệ thống"


async def record(
    uow: UnitOfWork,
    clock: Clock,
    actor: User,
    action: AuditAction,
    target_type: str,
    target_id: str,
    target_label: str,
    detail: dict[str, str] | None = None,
) -> None:
    await _append(
        uow, clock, actor.id, actor.email, action, target_type, target_id, target_label, detail
    )


async def record_system(
    uow: UnitOfWork,
    clock: Clock,
    action: AuditAction,
    target_type: str,
    target_id: str,
    target_label: str,
    detail: dict[str, str] | None = None,
) -> None:
    await _append(
        uow,
        clock,
        SYSTEM_ACTOR_ID,
        SYSTEM_ACTOR_LABEL,
        action,
        target_type,
        target_id,
        target_label,
        detail,
    )


async def _append(
    uow: UnitOfWork,
    clock: Clock,
    actor_id: str,
    actor_label: str,
    action: AuditAction,
    target_type: str,
    target_id: str,
    target_label: str,
    detail: dict[str, str] | None,
) -> None:
    await uow.audit.add(
        AuditEntry(
            id=new_id(),
            actor_id=actor_id,
            actor_email=actor_label,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_label=target_label,
            detail=detail or {},
            occurred_at=clock.now(),
        )
    )


def change(before: object, after: object) -> str:
    return f"{before} → {after}"
