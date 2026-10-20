from typing import Any

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

_MAX_PAGES = 3
_FALLBACK_REGION = "US"


def _unavailable(message: str) -> Exception:
    return ProviderUnavailable(message)


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
        thumbnail_url=as_text(covers[0]) if covers else None,
        duration_sec=as_int(media.get("duration")) // 1000,
    )


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
        self, handle: str, api_key: str, limit: int, user_id: str | None, region: str | None
    ) -> list[FetchedVideo]:
        collected: list[FetchedVideo] = []
        cursor: str | None = None
        for _ in range(_MAX_PAGES):
            params = {"handle": handle, "sort_by": "latest"}
            if user_id:
                params["user_id"] = user_id
            if region:
                params["region"] = region
            if cursor:
                params["max_cursor"] = cursor
            body = as_obj(await self._get("/v3/tiktok/profile/videos", params, api_key))
            for item in as_list(body.get("aweme_list")):
                parsed = _video(as_obj(item))
                if parsed is not None:
                    collected.append(parsed)
            cursor = as_text(body.get("max_cursor"))
            if len(collected) >= limit or not body.get("has_more") or cursor is None:
                break
        return collected[:limit]

    async def _videos_with_region_fallback(
        self, handle: str, api_key: str, limit: int, user_id: str | None
    ) -> list[FetchedVideo]:
        videos = await self._videos(handle, api_key, limit, user_id, None)
        if videos:
            return videos
        return await self._videos(handle, api_key, limit, user_id, _FALLBACK_REGION)

    async def fetch(self, request: FetchRequest) -> ProviderData:
        api_key = request.credentials.get("api_key", "")
        if not api_key:
            raise ProviderUnavailable("Chưa cấu hình API key của ScrapeCreators")
        profile = await self._profile(request.handle, api_key)
        try:
            videos = await self._videos_with_region_fallback(
                request.handle, api_key, request.max_videos, profile.platform_channel_id
            )
        except (ProviderError, ProviderUnavailable) as error:
            return ProviderData(
                profile=profile,
                videos=(),
                warning=f"Không lấy được danh sách video: {error.message}",
            )
        return ProviderData(profile=profile, videos=tuple(videos))
