from fastapi import APIRouter

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.analytics import PeriodDep
from vinichannels.adapters.inbound.http.schemas.scoring import (
    ScoreboardResponse,
    WeightsRequest,
    WeightsResponse,
)

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.get("")
async def scoreboard(
    user: CurrentUser, use_cases: UseCasesDep, period: PeriodDep
) -> ScoreboardResponse:
    result = await use_cases.get_scoreboard.execute(user, period)
    return ScoreboardResponse.model_validate(result)


@router.get("/weights")
async def get_weights(user: CurrentUser, use_cases: UseCasesDep) -> WeightsResponse:
    return WeightsResponse.model_validate(await use_cases.get_scoring_weights.execute(user))


@router.put("/weights")
async def update_weights(
    body: WeightsRequest, user: CurrentUser, use_cases: UseCasesDep
) -> WeightsResponse:
    updated = await use_cases.update_scoring_weights.execute(
        user, body.engagement, body.growth, body.reach, body.consistency
    )
    return WeightsResponse.model_validate(updated)
