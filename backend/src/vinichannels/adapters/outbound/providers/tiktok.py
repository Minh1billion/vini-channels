from datetime import timedelta
from typing import Any

import httpx

from vinichannels.adapters.outbound.providers.common import (
    Json,
    as_int,
    as_list,
    as_obj,
    as_text,
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
from vinichannels.application.ports.token_refresh import RefreshedToken, RefreshRequest
from vinichannels.domain.syncing.policies import SyncErrorKind
from vinichannels.domain.syncing.providers import ProviderKey

_USER_FIELDS = (
    "open_id,union_id,avatar_url,display_name,"
    "follower_count,following_count,likes_count,video_count"
)
_VIDEO_FIELDS = (
    "id,create_time,cover_image_url,share_url,video_description,duration,"
    "like_count,comment_count,share_count,view_count"
)
_PAGE_SIZE = 20
_TOKEN_CODES = {"access_token_invalid", "scope_not_authorized", "scope_permission_missed"}


def _raise_for(response: httpx.Response) -> Json:
    body = as_obj(read_json(response)) if response.content else {}
    error = as_obj(body.get("error"))
    code = as_text(error.get("code")) or "ok"
    message = as_text(error.get("message")) or f"Mã {response.status_code}"
    if response.status_code == 401 or code in _TOKEN_CODES:
        raise ProviderError(SyncErrorKind.TOKEN_REVOKED, "Token của kênh không còn hiệu lực")
    if response.status_code == 429 or code == "rate_limit_exceeded":
        raise ProviderError(SyncErrorKind.RATE_LIMITED, "TikTok đang giới hạn tần suất gọi")
    if response.status_code >= 400 or code != "ok":
        raise ProviderError(SyncErrorKind.SERVER_ERROR, f"TikTok báo lỗi: {message}")
    return body


def _video(item: Json) -> FetchedVideo | None:
    video_id = as_text(item.get("id"))
    posted_at = from_unix(item.get("create_time"))
    if video_id is None or posted_at is None:
        return None
    return FetchedVideo(
        platform_video_id=video_id,
        posted_at=posted_at,
        views=as_int(item.get("view_count")),
        likes=as_int(item.get("like_count")),
        comments=as_int(item.get("comment_count")),
        shares=as_int(item.get("share_count")),
        url=as_text(item.get("share_url")),
        caption=as_text(item.get("video_description")) or "",
        thumbnail_url=as_text(item.get("cover_image_url")),
        duration_sec=as_int(item.get("duration")),
    )


class TikTokProvider:
    key = ProviderKey.TIKTOK.value

    def __init__(
        self, client: httpx.AsyncClient, base_url: str = "https://open.tiktokapis.com"
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def _call(
        self, method: str, path: str, token: str, params: dict[str, str], body: Json | None = None
    ) -> Json:
        response = await send(
            self._client,
            method,
            f"{self._base_url}{path}",
            {"Authorization": f"Bearer {token}"},
            params,
            body,
        )
        return _raise_for(response)

    async def _profile(self, token: str) -> FetchedProfile:
        body = await self._call("GET", "/v2/user/info/", token, {"fields": _USER_FIELDS})
        user = as_obj(as_obj(body.get("data")).get("user"))
        return FetchedProfile(
            platform_channel_id=as_text(user.get("open_id")),
            display_name=as_text(user.get("display_name")),
            avatar_url=as_text(user.get("avatar_url")),
            followers=as_int(user.get("follower_count")),
            following=as_int(user.get("following_count")),
            total_likes=as_int(user.get("likes_count")),
            video_count=as_int(user.get("video_count")),
        )

    async def _videos(
        self, token: str, request: FetchRequest
    ) -> tuple[list[FetchedVideo], str | None]:
        collected: list[FetchedVideo] = []
        cursor: Any = None
        for page in range(request.max_pages):
            remaining = None if request.max_videos is None else request.max_videos - len(collected)
            payload: Json = {
                "max_count": _PAGE_SIZE if remaining is None else min(_PAGE_SIZE, remaining)
            }
            if cursor is not None:
                payload["cursor"] = cursor
            try:
                body = await self._call(
                    "POST", "/v2/video/list/", token, {"fields": _VIDEO_FIELDS}, payload
                )
            except ProviderError as error:
                if not collected or error.kind is SyncErrorKind.TOKEN_REVOKED:
                    raise
                return collected, f"Dừng ở trang {page + 1} do lỗi: {error.message}"
            data = as_obj(body.get("data"))
            fresh = [
                parsed
                for item in as_list(data.get("videos"))
                if (parsed := _video(as_obj(item))) is not None
            ]
            wanted = [v for v in fresh if request.since is None or v.posted_at >= request.since]
            collected.extend(wanted)
            cursor = data.get("cursor")
            passed_since = request.since is not None and bool(fresh) and not wanted
            full = request.max_videos is not None and len(collected) >= request.max_videos
            if full or passed_since or not data.get("has_more") or cursor is None:
                return collected, None
        return collected, f"Đã đạt giới hạn {request.max_pages} trang, có thể còn video cũ chưa lấy"

    async def fetch(self, request: FetchRequest) -> ProviderData:
        token = request.credentials.get("access_token", "")
        if not token:
            raise ProviderUnavailable("Kênh chưa có token TikTok")
        profile = await self._profile(token)
        try:
            videos, warning = await self._videos(token, request)
        except ProviderError as error:
            if error.kind is SyncErrorKind.TOKEN_REVOKED:
                raise
            return ProviderData(
                profile=profile,
                videos=(),
                warning=f"Không lấy được danh sách video: {error.message}",
            )
        return ProviderData(profile=profile, videos=tuple(videos), warning=warning)


class TikTokTokenRefresher:
    def __init__(
        self, client: httpx.AsyncClient, base_url: str = "https://open.tiktokapis.com"
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    async def refresh(self, request: RefreshRequest) -> RefreshedToken:
        try:
            response = await self._client.post(
                f"{self._base_url}/v2/oauth/token/",
                data={
                    "client_key": request.client_key,
                    "client_secret": request.client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": request.refresh_token,
                },
                headers={"Cache-Control": "no-cache"},
            )
        except httpx.TimeoutException as error:
            raise ProviderError(SyncErrorKind.NETWORK, "Hết thời gian chờ TikTok") from error
        except httpx.HTTPError as error:
            raise ProviderError(SyncErrorKind.NETWORK, "Không kết nối được TikTok") from error
        body = as_obj(read_json(response)) if response.content else {}
        error_code = as_text(body.get("error"))
        if error_code == "invalid_grant":
            raise ProviderError(SyncErrorKind.TOKEN_REVOKED, "Refresh token không còn hiệu lực")
        if response.status_code == 429:
            raise ProviderError(SyncErrorKind.RATE_LIMITED, "TikTok đang giới hạn tần suất gọi")
        access_token = as_text(body.get("access_token"))
        lifetime = as_int(body.get("expires_in"))
        if response.status_code >= 400 or error_code or access_token is None or lifetime <= 0:
            raise ProviderError(
                SyncErrorKind.SERVER_ERROR,
                f"TikTok báo lỗi khi gia hạn token ({error_code or response.status_code})",
            )
        refresh_lifetime = as_int(body.get("refresh_expires_in"))
        scope = as_text(body.get("scope")) or ""
        return RefreshedToken(
            access_token=access_token,
            lifetime=timedelta(seconds=lifetime),
            refresh_token=as_text(body.get("refresh_token")),
            refresh_lifetime=timedelta(seconds=refresh_lifetime) if refresh_lifetime else None,
            scopes=frozenset(item.strip() for item in scope.split(",") if item.strip()),
        )
