from typing import Annotated

from fastapi import APIRouter, Query

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.channels import ChannelResponse
from vinichannels.adapters.inbound.http.schemas.partners import PartnerResponse
from vinichannels.adapters.inbound.http.schemas.search import SearchResponse, SearchVideoResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search(
    user: CurrentUser,
    use_cases: UseCasesDep,
    q: Annotated[str, Query(max_length=100)] = "",
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> SearchResponse:
    result = await use_cases.global_search.execute(user, q, limit)
    return SearchResponse(
        partners=[PartnerResponse.model_validate(item) for item in result.partners],
        channels=[ChannelResponse.model_validate(item) for item in result.channels],
        videos=[SearchVideoResponse.model_validate(item) for item in result.videos],
    )
