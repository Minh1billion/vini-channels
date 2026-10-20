from datetime import date

from fastapi import APIRouter, Query

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.audit import AuditEntryResponse

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit(
    user: CurrentUser,
    use_cases: UseCasesDep,
    actor_id: str | None = None,
    action: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[AuditEntryResponse]:
    items = await use_cases.list_audit_log.execute(
        user, actor_id, action, date_from, date_to, limit, offset
    )
    return [AuditEntryResponse.model_validate(item) for item in items]
