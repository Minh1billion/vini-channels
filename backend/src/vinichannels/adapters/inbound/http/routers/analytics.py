from typing import Annotated

from fastapi import APIRouter, Query

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.analytics import (
    ChannelMetricsResponse,
    CompareResponse,
    OverviewResponse,
    PeriodDep,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview(
    user: CurrentUser, use_cases: UseCasesDep, period: PeriodDep
) -> OverviewResponse:
    result = await use_cases.get_overview.execute(user, period)
    return OverviewResponse.model_validate(result)


@router.get("/compare")
async def compare(
    user: CurrentUser,
    use_cases: UseCasesDep,
    channel_ids: Annotated[str, Query()],
    period: PeriodDep,
) -> CompareResponse:
    ids = [item.strip() for item in channel_ids.split(",") if item.strip()]
    results = await use_cases.compare_channels.execute(user, ids, period)
    return CompareResponse(
        range=period.label,
        channels=[ChannelMetricsResponse.model_validate(item) for item in results],
    )
