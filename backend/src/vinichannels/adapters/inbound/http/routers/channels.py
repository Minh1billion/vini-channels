from typing import Annotated

from fastapi import APIRouter, Query, status

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.analytics import (
    ChannelMetricsResponse,
    DailyViewsResponse,
    PeriodDep,
    TrendPointResponse,
    VideoGrowthResponse,
)
from vinichannels.adapters.inbound.http.schemas.channels import (
    ChannelCreateRequest,
    ChannelResponse,
    ChannelUpdateRequest,
    ScheduleRequest,
)
from vinichannels.adapters.inbound.http.schemas.common import given, given_nullable
from vinichannels.adapters.inbound.http.schemas.sync import CredentialRequest, SyncRunResponse
from vinichannels.application.use_cases.channels.crud import UpdateChannelCommand
from vinichannels.application.use_cases.channels.register import (
    ChannelToken,
    RegisterChannelCommand,
)

router = APIRouter(prefix="/channels", tags=["channels"])


@router.get("")
async def list_channels(
    user: CurrentUser,
    use_cases: UseCasesDep,
    partner_id: str | None = None,
    include_archived: bool = False,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[ChannelResponse]:
    items = await use_cases.list_channels.execute(user, partner_id, include_archived, q)
    return [ChannelResponse.model_validate(item) for item in items]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_channel(
    body: ChannelCreateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> ChannelResponse:
    token = (
        ChannelToken(body.token.access_token, body.token.expires_at, body.token.refresh_token)
        if body.token
        else None
    )
    created = await use_cases.register_channel.execute(
        user,
        RegisterChannelCommand(
            partner_id=body.partner_id,
            handle=body.handle,
            provider=body.provider,
            display_name=body.display_name,
            sync_cron=body.sync_cron,
            timezone=body.timezone,
            token=token,
        ),
    )
    return ChannelResponse.model_validate(created)


@router.get("/{channel_id}")
async def get_channel(
    channel_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> ChannelResponse:
    return ChannelResponse.model_validate(await use_cases.get_channel.execute(user, channel_id))


@router.get("/{channel_id}/metrics")
async def channel_metrics(
    channel_id: str,
    user: CurrentUser,
    use_cases: UseCasesDep,
    period: PeriodDep,
) -> ChannelMetricsResponse:
    result = await use_cases.get_channel_metrics.execute(user, channel_id, period)
    return ChannelMetricsResponse.model_validate(result)


@router.get("/{channel_id}/trend")
async def channel_trend(
    channel_id: str,
    user: CurrentUser,
    use_cases: UseCasesDep,
    period: PeriodDep,
) -> list[TrendPointResponse]:
    items = await use_cases.get_channel_trend.execute(user, channel_id, period)
    return [TrendPointResponse.model_validate(item) for item in items]


@router.get("/{channel_id}/daily-views")
async def channel_daily_views(
    channel_id: str,
    user: CurrentUser,
    use_cases: UseCasesDep,
    period: PeriodDep,
) -> list[DailyViewsResponse]:
    items = await use_cases.get_daily_views.execute(user, channel_id, period)
    return [DailyViewsResponse.model_validate(item) for item in items]


@router.get("/{channel_id}/video-growth")
async def channel_video_growth(
    channel_id: str,
    user: CurrentUser,
    use_cases: UseCasesDep,
    period: PeriodDep,
) -> list[VideoGrowthResponse]:
    items = await use_cases.get_video_growth.execute(user, channel_id, period)
    return [VideoGrowthResponse.model_validate(item) for item in items]


@router.patch("/{channel_id}")
async def update_channel(
    channel_id: str, body: ChannelUpdateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> ChannelResponse:
    command = UpdateChannelCommand(
        channel_id=channel_id,
        display_name=given(body.display_name),
        avatar_url=given_nullable(body, "avatar_url", body.avatar_url),
        is_active=given(body.is_active),
    )
    return ChannelResponse.model_validate(await use_cases.update_channel.execute(user, command))


@router.put("/{channel_id}/schedule")
async def set_schedule(
    channel_id: str, body: ScheduleRequest, user: CurrentUser, use_cases: UseCasesDep
) -> ChannelResponse:
    updated = await use_cases.set_channel_schedule.execute(
        user, channel_id, body.cron, body.timezone
    )
    return ChannelResponse.model_validate(updated)


@router.delete("/{channel_id}")
async def archive_channel(
    channel_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> ChannelResponse:
    return ChannelResponse.model_validate(await use_cases.archive_channel.execute(user, channel_id))


@router.post("/{channel_id}/restore")
async def restore_channel(
    channel_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> ChannelResponse:
    return ChannelResponse.model_validate(await use_cases.restore_channel.execute(user, channel_id))


@router.post("/{channel_id}/sync")
async def sync_channel(
    channel_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> SyncRunResponse:
    return SyncRunResponse.model_validate(await use_cases.sync_channel.execute(user, channel_id))


@router.put("/{channel_id}/credential")
async def set_credential(
    channel_id: str, body: CredentialRequest, user: CurrentUser, use_cases: UseCasesDep
) -> ChannelResponse:
    updated = await use_cases.set_channel_credential.execute(
        user, channel_id, body.access_token, body.expires_at, body.refresh_token
    )
    return ChannelResponse.model_validate(updated)
