from typing import Annotated, Literal

from fastapi import APIRouter, Query, Response

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.analytics import (
    PeriodDep,
    VideoResponse,
)
from vinichannels.application.use_cases.analytics.metrics import VideoSort

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("")
async def list_videos(
    user: CurrentUser,
    use_cases: UseCasesDep,
    period: PeriodDep,
    response: Response,
    channel_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str | None, Query(max_length=100)] = None,
    sort: VideoSort = VideoSort.POSTED,
    order: Literal["asc", "desc"] = "desc",
) -> list[VideoResponse]:
    page = await use_cases.list_videos.page(
        user, channel_id, period, limit, offset, q, sort, order == "desc"
    )
    response.headers["X-Total-Count"] = str(page.total)
    return [VideoResponse.model_validate(item) for item in page.items]
