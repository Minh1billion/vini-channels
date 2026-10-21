import asyncio
from dataclasses import replace

from vinichannels.application.ports.data_provider import FetchedVideo, ProviderData
from vinichannels.application.ports.thumbnails import THUMBNAIL_PATH, ThumbnailStore
from vinichannels.application.progress import Progress

_CONCURRENCY = 8
_BATCH = 25


async def mirror_thumbnails(
    store: ThumbnailStore | None, data: ProviderData, progress: Progress | None = None
) -> ProviderData:
    """Thay URL ảnh bìa của nhà cung cấp (hay hết hạn) bằng URL ảnh đã lưu của mình.

    Không bao giờ làm hỏng lần đồng bộ: ảnh nào không lưu được thì giữ URL gốc.
    """
    if store is None or not data.videos:
        return data
    gate = asyncio.Semaphore(_CONCURRENCY)

    async def one(video: FetchedVideo) -> FetchedVideo:
        source = video.thumbnail_url
        if not source or source.startswith(THUMBNAIL_PATH):
            return video
        async with gate:
            local = await store.mirror(video.platform_video_id, source)
        return video if local is None else replace(video, thumbnail_url=local)

    videos = list(data.videos)
    pending = [
        index
        for index, video in enumerate(videos)
        if video.thumbnail_url and not video.thumbnail_url.startswith(THUMBNAIL_PATH)
    ]
    for start in range(0, len(pending), _BATCH):
        batch = pending[start : start + _BATCH]
        results = await asyncio.gather(*(one(videos[index]) for index in batch))
        for index, video in zip(batch, results, strict=True):
            videos[index] = video
        if progress is not None:
            await progress("Đang lưu ảnh bìa", start + len(batch), len(pending))
    return replace(data, videos=tuple(videos))
