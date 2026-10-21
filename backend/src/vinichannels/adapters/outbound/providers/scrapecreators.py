from typing import Any, NamedTuple

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

_FALLBACK_REGION = "US"


class _Feed(NamedTuple):
    videos: list[FetchedVideo]
    seen: int
    warning: str | None


def _unavailable(message: str) -> Exception:
    return ProviderUnavailable(message)


def _pick_cover(urls: list[object]) -> str | None:
    texts = [text for text in (as_text(url) for url in urls) if text]
    for text in texts:
        if not text.split("?")[0].lower().endswith(".heic"):
            return text
    return texts[0] if texts else None


def _video(item: Json) -> FetchedVideo | None:
    video_id = as_text(item.get("aweme_id"))
    posted_at = from_unix(item.get("create_time"))
    if video_id is None or posted_at is None:
        return None
    stats = as_obj(item.get("statistics"))
    media = as_obj(item.get("video"))
    covers = as_list(as_obj(media.get("cover")).get("url_list"))
    return FetchedVideo(
        platform_video_id=video_id,
        posted_at=posted_at,
        views=as_int(stats.get("play_count")),
        likes=as_int(stats.get("digg_count")),
        comments=as_int(stats.get("comment_count")),
        shares=as_int(stats.get("share_count")),
        saves=as_int(stats.get("collect_count")) if "collect_count" in stats else None,
        url=as_text(item.get("share_url")),
        caption=as_text(item.get("desc")) or "",
        thumbnail_url=_pick_cover(covers),
        duration_sec=as_int(media.get("duration")) // 1000,
    )


def _capped(videos: list[FetchedVideo], request: FetchRequest) -> list[FetchedVideo]:
    return videos if request.max_videos is None else videos[: request.max_videos]


class ScrapeCreatorsProvider:
    key = ProviderKey.SCRAPECREATORS.value

    def __init__(
        self, client: httpx.AsyncClient, base_url: str = "https://api.scrapecreators.com"
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def _get(self, path: str, params: dict[str, str], api_key: str) -> Any:
        response = await send(
            self._client, "GET", f"{self._base_url}{path}", {"x-api-key": api_key}, params
        )
        check_status(response, _unavailable)
        return read_json(response)

    async def _profile(self, handle: str, api_key: str) -> FetchedProfile:
        body = as_obj(await self._get("/v1/tiktok/profile", {"handle": handle}, api_key))
        user = as_obj(body.get("user"))
        if not user:
            raise ProviderError(SyncErrorKind.NOT_FOUND, "Không tìm thấy kênh trên nguồn này")
        exact = as_obj(body.get("statsV2"))
        rounded = as_obj(body.get("stats"))

        def count(name: str) -> int:
            return as_int(exact.get(name)) or as_int(rounded.get(name))

        return FetchedProfile(
            platform_channel_id=as_text(user.get("id")),
            display_name=as_text(user.get("nickname")),
            avatar_url=as_text(user.get("avatarLarger")) or as_text(user.get("avatarMedium")),
            followers=count("followerCount"),
            following=count("followingCount"),
            total_likes=count("heartCount"),
            video_count=count("videoCount"),
        )

    async def _videos(
        self,
        handle: str,
        api_key: str,
        request: FetchRequest,
        user_id: str | None,
        region: str | None,
    ) -> _Feed:
        collected: list[FetchedVideo] = []
        seen = 0
        cursor: str | None = None
        for page in range(request.max_pages):
            params = {"handle": handle, "sort_by": "latest"}
            if user_id:
                params["user_id"] = user_id
            if region:
                params["region"] = region
            if cursor:
                params["max_cursor"] = cursor
            try:
                body = as_obj(await self._get("/v3/tiktok/profile/videos", params, api_key))
            except (ProviderError, ProviderUnavailable) as error:
                if not collected:
                    raise
                warning = f"Dừng ở trang {page + 1} do lỗi: {error.message}"
                return _Feed(_capped(collected, request), seen, warning)
            fresh = [
                parsed
                for item in as_list(body.get("aweme_list"))
                if (parsed := _video(as_obj(item))) is not None
            ]
            seen += len(fresh)
            wanted = [v for v in fresh if request.since is None or v.posted_at >= request.since]
            collected.extend(wanted)
            if request.progress is not None:
                await request.progress("Đang lấy dữ liệu", len(collected), None)
            cursor = as_text(body.get("max_cursor"))
            passed_since = request.since is not None and bool(fresh) and not wanted
            full = request.max_videos is not None and len(collected) >= request.max_videos
            if full or passed_since or not body.get("has_more") or cursor is None:
                return _Feed(_capped(collected, request), seen, None)
        warning = f"Đã đạt giới hạn {request.max_pages} trang, có thể còn video cũ chưa lấy"
        return _Feed(_capped(collected, request), seen, warning)

    async def _videos_with_region_fallback(
        self, handle: str, api_key: str, request: FetchRequest, user_id: str | None
    ) -> _Feed:
        feed = await self._videos(handle, api_key, request, user_id, None)
        if feed.seen:
            return feed
        return await self._videos(handle, api_key, request, user_id, _FALLBACK_REGION)

    async def fetch(self, request: FetchRequest) -> ProviderData:
        api_key = request.credentials.get("api_key", "")
        if not api_key:
            raise ProviderUnavailable("Chưa cấu hình API key của ScrapeCreators")
        profile = await self._profile(request.handle, api_key)
        try:
            feed = await self._videos_with_region_fallback(
                request.handle, api_key, request, profile.platform_channel_id
            )
        except (ProviderError, ProviderUnavailable) as error:
            return ProviderData(
                profile=profile,
                videos=(),
                warning=f"Không lấy được danh sách video: {error.message}",
            )
        return ProviderData(profile=profile, videos=tuple(feed.videos), warning=feed.warning)
