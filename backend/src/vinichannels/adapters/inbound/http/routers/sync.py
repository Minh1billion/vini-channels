from typing import Annotated

from fastapi import APIRouter, Query

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.sync import SyncRunResponse, SyncScheduleResponse
from vinichannels.domain.syncing.entities import SyncStatus

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/runs")
async def list_runs(
    user: CurrentUser,
    use_cases: UseCasesDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    status: SyncStatus | None = None,
    channel_id: str | None = None,
) -> list[SyncRunResponse]:
    items = await use_cases.list_sync_runs.execute(user, limit, status, channel_id)
    return [SyncRunResponse.model_validate(item) for item in items]


@router.get("/schedules")
async def list_schedules(user: CurrentUser, use_cases: UseCasesDep) -> list[SyncScheduleResponse]:
    items = await use_cases.list_sync_schedules.execute(user)
    return [SyncScheduleResponse.model_validate(item) for item in items]
