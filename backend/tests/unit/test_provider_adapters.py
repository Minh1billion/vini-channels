import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

import httpx
import pytest

from vinichannels.adapters.outbound.providers.apify import ApifyProvider
from vinichannels.adapters.outbound.providers.scrapecreators import ScrapeCreatorsProvider
from vinichannels.adapters.outbound.providers.tiktok import TikTokProvider, TikTokTokenRefresher
from vinichannels.application.ports.data_provider import (
    FetchRequest,
    ProviderData,
    ProviderError,
    ProviderUnavailable,
)
from vinichannels.application.ports.token_refresh import RefreshRequest
from vinichannels.domain.syncing.policies import SyncErrorKind

NOW = datetime(2026, 10, 19, 7, 0, tzinfo=UTC)


def _request(**credentials: str) -> FetchRequest:
    return FetchRequest("alpha.vn", None, credentials, 10, NOW)


def _fetch(provider: object, request: FetchRequest) -> ProviderData:
    return asyncio.run(provider.fetch(request))  # type: ignore[attr-defined]


def _client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=handler)


def test_scrapecreators_parses_profile_and_videos() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "key"
        if request.url.path == "/v1/tiktok/profile":
            return httpx.Response(
                200,
                json={
                    "user": {"id": "1", "nickname": "Alpha", "avatarLarger": "http://a"},
                    "stats": {
                        "followerCount": 10,
                        "followingCount": 2,
                        "heartCount": 5,
                        "videoCount": 3,
                    },
                },
            )
        return httpx.Response(
            200,
            json={
                "aweme_list": [
                    {
                        "aweme_id": "9",
                        "desc": "hi",
                        "create_time": 1_760_000_000,
                        "video": {"duration": 15000, "cover": {"url_list": ["http://c"]}},
                        "statistics": {
                            "play_count": 100,
                            "digg_count": 5,
                            "comment_count": 1,
                            "share_count": 2,
                            "collect_count": 3,
                        },
                    },
                    {"aweme_id": "bad"},
                ],
                "has_more": False,
            },
        )

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(handler))), _request(api_key="key")
    )
    assert data.profile.followers == 10
    assert data.warning is None
    assert len(data.videos) == 1
    video = data.videos[0]
    assert (video.views, video.saves, video.duration_sec) == (100, 3, 15)


def test_scrapecreators_errors_map_to_domain_kinds() -> None:
    def status(code: int) -> ScrapeCreatorsProvider:
        return ScrapeCreatorsProvider(
            _client(httpx.MockTransport(lambda _: httpx.Response(code, json={})))
        )

    with pytest.raises(ProviderUnavailable):
        _fetch(status(401), _request(api_key="k"))
    with pytest.raises(ProviderError) as missing:
        _fetch(status(404), _request(api_key="k"))
    assert missing.value.kind is SyncErrorKind.NOT_FOUND
    with pytest.raises(ProviderError) as limited:
        _fetch(status(429), _request(api_key="k"))
    assert limited.value.kind is SyncErrorKind.RATE_LIMITED
    with pytest.raises(ProviderUnavailable):
        _fetch(status(200), _request())


def test_scrapecreators_videos_failure_is_partial() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/tiktok/profile":
            return httpx.Response(200, json={"user": {"id": "1"}, "stats": {"followerCount": 7}})
        return httpx.Response(500)

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(handler))), _request(api_key="k")
    )
    assert data.profile.followers == 7
    assert data.videos == ()
    assert data.warning is not None


def test_scrapecreators_prefers_exact_stats_v2() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/tiktok/profile":
            return httpx.Response(
                200,
                json={
                    "user": {"id": "1"},
                    "stats": {"followerCount": 194300, "videoCount": 15},
                    "statsV2": {"followerCount": "194286", "videoCount": "15"},
                },
            )
        return httpx.Response(200, json={"aweme_list": []})

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(handler))), _request(api_key="k")
    )
    assert data.profile.followers == 194286
    assert data.profile.video_count == 15


def test_scrapecreators_retries_empty_feed_with_region() -> None:
    regions: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/tiktok/profile":
            return httpx.Response(200, json={"user": {"id": "9"}, "stats": {"followerCount": 3}})
        regions.append(request.url.params.get("region"))
        assert request.url.params.get("user_id") == "9"
        if request.url.params.get("region") != "US":
            return httpx.Response(200, json={"aweme_list": []})
        item = {"aweme_id": "5", "create_time": 1_760_000_000, "statistics": {"play_count": 8}}
        return httpx.Response(200, json={"aweme_list": [item], "has_more": 0})

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(handler))), _request(api_key="k")
    )
    assert regions == [None, "US"]
    assert [video.views for video in data.videos] == [8]


def _feed_handler(pages: list[dict[str, object]], calls: list[str | None]):  # type: ignore[no-untyped-def]
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/tiktok/profile":
            return httpx.Response(200, json={"user": {"id": "1"}, "stats": {"followerCount": 1}})
        cursor = request.url.params.get("max_cursor")
        calls.append(cursor)
        return httpx.Response(200, json=pages[len(calls) - 1])

    return handler


def _item(video_id: str, created: int) -> dict[str, object]:
    return {"aweme_id": video_id, "create_time": created, "statistics": {"play_count": 1}}


DAY = 86_400
BASE = int(NOW.timestamp())


def test_scrapecreators_follows_cursors_until_history_ends() -> None:
    calls: list[str | None] = []
    pages = [
        {
            "aweme_list": [_item("a", BASE - DAY), _item("b", BASE - 2 * DAY)],
            "has_more": 1,
            "max_cursor": "c1",
        },
        {"aweme_list": [_item("c", BASE - 3 * DAY)], "has_more": 1, "max_cursor": "c2"},
        {"aweme_list": [_item("d", BASE - 400 * DAY)], "has_more": 0, "max_cursor": "c3"},
    ]
    request = FetchRequest("alpha.vn", None, {"api_key": "k"}, None, NOW, None, 10)

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(_feed_handler(pages, calls)))), request
    )

    assert calls == [None, "c1", "c2"]
    assert [video.platform_video_id for video in data.videos] == ["a", "b", "c", "d"]
    assert data.warning is None


def test_scrapecreators_stops_once_a_page_is_older_than_since() -> None:
    calls: list[str | None] = []
    pages = [
        {
            "aweme_list": [_item("a", BASE - DAY), _item("b", BASE - 10 * DAY)],
            "has_more": 1,
            "max_cursor": "c1",
        },
        {
            "aweme_list": [_item("c", BASE - 20 * DAY), _item("d", BASE - 30 * DAY)],
            "has_more": 1,
            "max_cursor": "c2",
        },
        {"aweme_list": [_item("e", BASE - 40 * DAY)], "has_more": 1, "max_cursor": "c3"},
    ]
    since = datetime.fromtimestamp(BASE - 15 * DAY, UTC)
    request = FetchRequest("alpha.vn", None, {"api_key": "k"}, None, NOW, since, 10)

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(_feed_handler(pages, calls)))), request
    )

    assert calls == [None, "c1"]
    assert [video.platform_video_id for video in data.videos] == ["a", "b"]
    assert data.warning is None


def test_scrapecreators_does_not_retry_region_when_since_filters_everything() -> None:
    calls: list[str | None] = []
    pages = [{"aweme_list": [_item("a", BASE - 90 * DAY)], "has_more": 1, "max_cursor": "c1"}]
    since = datetime.fromtimestamp(BASE - 7 * DAY, UTC)
    request = FetchRequest("alpha.vn", None, {"api_key": "k"}, None, NOW, since, 10)

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(_feed_handler(pages, calls)))), request
    )

    assert calls == [None]
    assert data.videos == ()


def test_scrapecreators_warns_when_page_cap_is_reached() -> None:
    calls: list[str | None] = []
    pages = [
        {"aweme_list": [_item(str(n), BASE - n * DAY)], "has_more": 1, "max_cursor": f"c{n}"}
        for n in range(1, 4)
    ]
    request = FetchRequest("alpha.vn", None, {"api_key": "k"}, None, NOW, None, 2)

    data = _fetch(
        ScrapeCreatorsProvider(_client(httpx.MockTransport(_feed_handler(pages, calls)))), request
    )

    assert len(calls) == 2
    assert len(data.videos) == 2
    assert data.warning is not None


def test_scrapecreators_keeps_collected_pages_when_a_later_page_fails() -> None:
    calls: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/tiktok/profile":
            return httpx.Response(200, json={"user": {"id": "1"}, "stats": {"followerCount": 1}})
        calls.append(request.url.params.get("max_cursor"))
        if len(calls) == 1:
            return httpx.Response(
                200,
                json={"aweme_list": [_item("a", BASE - DAY)], "has_more": 1, "max_cursor": "c1"},
            )
        return httpx.Response(500)

    request = FetchRequest("alpha.vn", None, {"api_key": "k"}, None, NOW, None, 10)

    data = _fetch(ScrapeCreatorsProvider(_client(httpx.MockTransport(handler))), request)

    assert [video.platform_video_id for video in data.videos] == ["a"]
    assert data.warning is not None


def test_apify_parses_items_and_flags_private() -> None:
    items = [
        {
            "id": "7",
            "text": "cap",
            "createTime": 1_760_000_000,
            "webVideoUrl": "http://v",
            "playCount": 50,
            "diggCount": 4,
            "commentCount": 1,
            "shareCount": 1,
            "videoMeta": {"duration": 20, "coverUrl": "http://c"},
            "authorMeta": {
                "id": "5",
                "nickName": "Alpha",
                "avatar": "http://a",
                "fans": 99,
                "following": 1,
                "heart": 10,
                "video": 2,
            },
        }
    ]
    seen: list[httpx.Request] = []

    def ok(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=items)

    data = _fetch(
        ApifyProvider(_client(httpx.MockTransport(ok))), _request(api_token="t", actor_id="a/b")
    )
    assert seen[0].url.path == "/v2/acts/a~b/run-sync-get-dataset-items"
    assert seen[0].headers["authorization"] == "Bearer t"
    assert data.profile.followers == 99
    assert data.videos[0].views == 50

    private = ApifyProvider(
        _client(
            httpx.MockTransport(
                lambda _: httpx.Response(201, json=[{"error": "Profile is private"}])
            )
        )
    )
    with pytest.raises(ProviderError) as error:
        _fetch(private, _request(api_token="t"))
    assert error.value.kind is SyncErrorKind.PRIVATE

    gone = ApifyProvider(_client(httpx.MockTransport(lambda _: httpx.Response(404))))
    with pytest.raises(ProviderUnavailable):
        _fetch(gone, _request(api_token="t"))


def test_tiktok_parses_and_maps_token_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer tok"
        if request.url.path == "/v2/user/info/":
            return httpx.Response(
                200,
                json={
                    "data": {
                        "user": {
                            "open_id": "o",
                            "display_name": "A",
                            "follower_count": 42,
                            "video_count": 1,
                        }
                    },
                    "error": {"code": "ok"},
                },
            )
        return httpx.Response(
            200,
            json={
                "data": {
                    "videos": [
                        {
                            "id": "1",
                            "create_time": 1_760_000_000,
                            "view_count": 10,
                            "like_count": 1,
                            "comment_count": 0,
                            "share_count": 0,
                            "duration": 9,
                        }
                    ],
                    "has_more": False,
                },
                "error": {"code": "ok"},
            },
        )

    data = _fetch(
        TikTokProvider(_client(httpx.MockTransport(handler))), _request(access_token="tok")
    )
    assert data.profile.followers == 42
    assert data.videos[0].saves is None

    revoked = TikTokProvider(
        _client(
            httpx.MockTransport(
                lambda _: httpx.Response(401, json={"error": {"code": "access_token_invalid"}})
            )
        )
    )
    with pytest.raises(ProviderError) as error:
        _fetch(revoked, _request(access_token="tok"))
    assert error.value.kind is SyncErrorKind.TOKEN_REVOKED


def _refresh_client(handler: Callable[[httpx.Request], httpx.Response]) -> TikTokTokenRefresher:
    return TikTokTokenRefresher(httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def test_tiktok_refresher_sends_form_and_parses_token() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "access_token": "a2",
                "expires_in": 86400,
                "refresh_token": "r2",
                "refresh_expires_in": 31536000,
                "scope": "user.info.basic,video.list",
            },
        )

    token = asyncio.run(_refresh_client(handler).refresh(RefreshRequest("r1", "ck", "cs")))
    assert seen[0].url.path == "/v2/oauth/token/"
    assert b"grant_type=refresh_token" in seen[0].content and b"refresh_token=r1" in seen[0].content
    assert token.access_token == "a2" and token.refresh_token == "r2"
    assert token.lifetime.total_seconds() == 86400
    assert token.scopes == {"user.info.basic", "video.list"}


def test_tiktok_refresher_maps_invalid_grant_to_revoked_and_5xx_to_transient() -> None:
    revoked = _refresh_client(lambda _: httpx.Response(400, json={"error": "invalid_grant"}))
    with pytest.raises(ProviderError) as caught:
        asyncio.run(revoked.refresh(RefreshRequest("r1", "ck", "cs")))
    assert caught.value.kind is SyncErrorKind.TOKEN_REVOKED
    broken = _refresh_client(lambda _: httpx.Response(500, json={}))
    with pytest.raises(ProviderError) as transient:
        asyncio.run(broken.refresh(RefreshRequest("r1", "ck", "cs")))
    assert transient.value.kind.is_transient
