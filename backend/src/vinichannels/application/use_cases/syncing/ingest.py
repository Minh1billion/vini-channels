import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime

from vinichannels.application.ports.data_provider import (
    DataProvider,
    FetchRequest,
    ProviderData,
    ProviderError,
)
from vinichannels.application.ports.unit_of_work import UnitOfWork
from vinichannels.domain.channels.entities import Channel
from vinichannels.domain.channels.value_objects import ChannelStatus
from vinichannels.domain.content.entities import Video
from vinichannels.domain.content.snapshots import ChannelSnapshot, VideoSnapshot
from vinichannels.domain.shared.ids import VideoId, new_id
from vinichannels.domain.syncing.policies import RetryPolicy

Sleep = Callable[[float], Awaitable[None]]

_RECOVERABLE = {ChannelStatus.PROVIDER_ERROR, ChannelStatus.PRIVATE, ChannelStatus.NOT_FOUND}


async def fetch_with_retry(
    provider: DataProvider,
    request: FetchRequest,
    retry: RetryPolicy,
    sleep: Sleep = asyncio.sleep,
) -> ProviderData:
    attempt = 1
    while True:
        try:
            return await provider.fetch(request)
        except ProviderError as error:
            if not retry.should_retry(attempt, error.kind):
                raise
            await sleep(retry.delay_for(attempt))
            attempt += 1


async def store_data(
    uow: UnitOfWork, channel: Channel, data: ProviderData, source: str, at: datetime
) -> None:
    profile = data.profile
    if profile.platform_channel_id:
        channel.platform_channel_id = profile.platform_channel_id
    if profile.avatar_url:
        channel.avatar_url = profile.avatar_url
    if profile.display_name and channel.display_name == channel.handle.display:
        channel.display_name = profile.display_name
    if channel.status in _RECOVERABLE:
        channel.change_status(ChannelStatus.HEALTHY, at)
    await uow.channels.save(channel)
    await uow.snapshots.add_channel_snapshot(
        ChannelSnapshot(
            channel_id=channel.id,
            captured_at=at,
            source=source,
            followers=profile.followers,
            following=profile.following,
            total_likes=profile.total_likes,
            video_count=profile.video_count,
        )
    )
    fetched = {video.platform_video_id: video for video in data.videos}
    existing = await uow.videos.get_by_platform_ids(channel.id, list(fetched))
    snapshots: list[VideoSnapshot] = []
    for item in fetched.values():
        video = existing.get(item.platform_video_id) or Video(
            id=VideoId(new_id()),
            channel_id=channel.id,
            platform_video_id=item.platform_video_id,
            posted_at=item.posted_at,
        )
        video.url = item.url or video.url
        video.caption = item.caption
        video.thumbnail_url = item.thumbnail_url or video.thumbnail_url
        video.duration_sec = item.duration_sec
        await uow.videos.save(video)
        snapshots.append(
            VideoSnapshot(
                video_id=video.id,
                captured_at=at,
                source=source,
                views=item.views,
                likes=item.likes,
                comments=item.comments,
                shares=item.shares,
                saves=item.saves,
            )
        )
    await uow.snapshots.add_video_snapshots(snapshots)
