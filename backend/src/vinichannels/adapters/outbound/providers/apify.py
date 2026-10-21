import httpx

from vinichannels.adapters.outbound.providers.common import (
    Json,
    as_int,
    as_list,
    as_obj,
    as_text,
    check_status,
    from_unix,
    read_json,
    send,
)
from vinichannels.application.ports.data_provider import (
    FetchedProfile,
    FetchedVideo,
    FetchRequest,
    ProviderData,
    ProviderError,
    ProviderUnavailable,
)
from vinichannels.domain.syncing.policies import SyncErrorKind
from vinichannels.domain.syncing.providers import ProviderKey

DEFAULT_ACTOR = "clockworks/tiktok-scraper"
UNBOUNDED_RESULTS = 1000


def _unavailable(message: str) -> Exception:
    return ProviderUnavailable(message)


def _video(item: Json) -> FetchedVideo | None:
    video_id = as_text(item.get("id"))
    posted_at = from_unix(item.get("createTime"))
    if video_id is None or posted_at is None:
        return None
    meta = as_obj(item.get("videoMeta"))
    return FetchedVideo(
        platform_video_id=video_id,
        posted_at=posted_at,
        views=as_int(item.get("playCount")),
        likes=as_int(item.get("diggCount")),
        comments=as_int(item.get("commentCount")),
        shares=as_int(item.get("shareCount")),
        saves=as_int(item.get("collectCount")) if "collectCount" in item else None,
        url=as_text(item.get("webVideoUrl")),
        caption=as_text(item.get("text")) or "",
        thumbnail_url=as_text(meta.get("coverUrl")),
        duration_sec=as_int(meta.get("duration")),
    )


def _profile(author: Json) -> FetchedProfile:
    return FetchedProfile(
        platform_channel_id=as_text(author.get("id")),
        display_name=as_text(author.get("nickName")),
        avatar_url=as_text(author.get("avatar")),
        followers=as_int(author.get("fans")),
        following=as_int(author.get("following")),
        total_likes=as_int(author.get("heart")),
        video_count=as_int(author.get("video")),
    )


def _failure(items: list[Json]) -> ProviderError:
    text = " ".join(as_text(item.get("error")) or "" for item in items).lower()
    if "private" in text:
        return ProviderError(SyncErrorKind.PRIVATE, "Kênh ở chế độ riêng tư")
    return ProviderError(SyncErrorKind.NOT_FOUND, "Không có dữ liệu cho kênh này")


class ApifyProvider:
    key = ProviderKey.APIFY.value

    def __init__(self, client: httpx.AsyncClient, base_url: str = "https://api.apify.com") -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def fetch(self, request: FetchRequest) -> ProviderData:
        token = request.credentials.get("api_token", "")
        if not token:
            raise ProviderUnavailable("Chưa cấu hình token của Apify")
        actor = (request.credentials.get("actor_id") or DEFAULT_ACTOR).replace("/", "~")
        response = await send(
            self._client,
            "POST",
            f"{self._base_url}/v2/acts/{actor}/run-sync-get-dataset-items",
            {"Authorization": f"Bearer {token}"},
            body={
                "profiles": [request.handle],
                "resultsPerPage": request.max_videos or UNBOUNDED_RESULTS,
                "shouldDownloadVideos": False,
                "shouldDownloadCovers": False,
                "shouldDownloadSubtitles": False,
            },
        )
        check_status(response, _unavailable, missing_is_channel=False)
        items = [as_obj(item) for item in as_list(read_json(response))]
        valid = [item for item in items if as_text(item.get("id")) and item.get("authorMeta")]
        if not valid:
            raise _failure(items)
        videos = [
            parsed
            for item in valid
            if (parsed := _video(item)) is not None
            and (request.since is None or parsed.posted_at >= request.since)
        ]
        limit = request.max_videos or UNBOUNDED_RESULTS
        return ProviderData(
            profile=_profile(as_obj(valid[0].get("authorMeta"))),
            videos=tuple(videos[:limit]),
        )
