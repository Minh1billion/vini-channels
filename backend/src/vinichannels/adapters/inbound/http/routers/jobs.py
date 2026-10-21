from fastapi import APIRouter, status

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.routers.channels import register_command
from vinichannels.adapters.inbound.http.schemas.channels import ChannelCreateRequest
from vinichannels.adapters.inbound.http.schemas.sync import FetchJobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(user: CurrentUser, use_cases: UseCasesDep) -> list[FetchJobResponse]:
    items = await use_cases.list_fetch_jobs.execute(user)
    return [FetchJobResponse.model_validate(item) for item in items]


@router.post("/channels", status_code=status.HTTP_202_ACCEPTED)
async def register_channel(
    body: ChannelCreateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> FetchJobResponse:
    job = await use_cases.start_register_channel.execute(user, register_command(body))
    return FetchJobResponse.model_validate(job)


@router.post("/channels/{channel_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_channel(
    channel_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> FetchJobResponse:
    job = await use_cases.start_sync_channel.execute(user, channel_id)
    return FetchJobResponse.model_validate(job)
