from collections.abc import Iterator

import httpx
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("argon2")

from fastapi.testclient import TestClient

from vinichannels.bootstrap.container import build_app
from vinichannels.bootstrap.settings import Settings

ADMIN = {"email": "admin@example.com", "password": "password123"}


def _scrapecreators_api(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/v1/tiktok/profile":
        return httpx.Response(
            200,
            json={
                "user": {
                    "id": "1",
                    "nickname": "Alpha Shop",
                    "avatarLarger": "http://a/avatar.png",
                },
                "stats": {
                    "followerCount": 1200,
                    "followingCount": 5,
                    "heartCount": 900,
                    "videoCount": 2,
                },
            },
        )
    return httpx.Response(
        200,
        json={
            "aweme_list": [
                {
                    "aweme_id": str(video_id),
                    "desc": f"video {video_id}",
                    "create_time": 1_760_000_000 + video_id,
                    "video": {"duration": 15000},
                    "statistics": {
                        "play_count": 100 * video_id,
                        "digg_count": 10,
                        "comment_count": 1,
                        "share_count": 2,
                        "collect_count": 3,
                    },
                }
                for video_id in (1, 2)
            ],
            "has_more": False,
        },
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key-with-at-least-32-bytes!!",
        admin_email=ADMIN["email"],
        admin_password=ADMIN["password"],
        sync_lookback_days=0,
    )
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(_scrapecreators_api))
    with TestClient(build_app(settings, http_client)) as test_client:
        yield test_client


def _enable_scrapecreators(client: TestClient) -> None:
    response = client.put(
        "/api/v1/providers/scrapecreators",
        json={"credentials": {"api_key": "secret-value"}, "enabled": True},
    )
    assert response.status_code == 200, response.text


def _login(client: TestClient, email: str, password: str) -> None:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text


def test_requires_login_and_rejects_bad_credentials(client: TestClient) -> None:
    assert client.get("/api/v1/partners").status_code == 401
    bad = client.post("/api/v1/auth/login", json={"email": ADMIN["email"], "password": "nope"})
    assert bad.status_code == 401
    assert bad.json()["code"] == "unauthorized"
    _login(client, **ADMIN)
    assert client.get("/api/v1/me").json()["role"] == "admin"
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/me").status_code == 401


def test_partner_and_channel_flow(client: TestClient) -> None:
    _login(client, **ADMIN)
    _enable_scrapecreators(client)
    created = client.post(
        "/api/v1/partners", json={"name": "Alpha", "industry": "Food", "tags": ["VN"]}
    )
    assert created.status_code == 201
    partner = created.json()
    assert partner["tags"] == ["vn"]
    assert client.post("/api/v1/partners", json={"name": "alpha"}).status_code == 409

    channel = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "@Alpha.VN", "provider": "scrapecreators"},
    )
    assert channel.status_code == 201
    assert channel.json()["handle"] == "alpha.vn"
    assert (
        client.post(
            "/api/v1/channels",
            json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
        ).status_code
        == 409
    )

    scheduled = client.put(
        f"/api/v1/channels/{channel.json()['id']}/schedule",
        json={"cron": "0 */6 * * *", "timezone": "Asia/Bangkok"},
    )
    assert scheduled.json()["sync_cron"] == "0 */6 * * *"
    bad_cron = client.put(
        f"/api/v1/channels/{channel.json()['id']}/schedule", json={"cron": "oops"}
    )
    assert bad_cron.status_code == 422

    patched = client.patch(f"/api/v1/partners/{partner['id']}", json={"industry": None})
    assert patched.json()["industry"] is None
    assert patched.json()["name"] == "Alpha"
    assert client.get("/api/v1/partners").json()[0]["channel_count"] == 1

    rejected = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "two.vn", "provider": "apify"},
    )
    assert rejected.status_code == 409
    unknown = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "two.vn", "provider": "nope"},
    )
    assert unknown.status_code == 422
    removed = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "two.vn", "provider": "mock"},
    )
    assert removed.status_code == 422
    assert client.post("/api/v1/channels/import", json={"content": ""}).status_code in (404, 405)
    assert len(client.get("/api/v1/channels").json()) == 1

    archived = client.delete(f"/api/v1/partners/{partner['id']}")
    assert archived.json()["archived_at"] is not None
    assert client.get("/api/v1/channels").json() == []


def test_viewer_is_read_only(client: TestClient) -> None:
    _login(client, **ADMIN)
    made = client.post(
        "/api/v1/users",
        json={"email": "v@example.com", "password": "password123", "role": "viewer"},
    )
    assert made.status_code == 201
    client.post("/api/v1/auth/logout")
    _login(client, "v@example.com", "password123")
    assert client.get("/api/v1/partners").status_code == 200
    assert client.post("/api/v1/partners", json={"name": "X"}).status_code == 403
    assert client.get("/api/v1/users").status_code == 403


def test_provider_settings_and_manual_sync(client: TestClient) -> None:
    _login(client, **ADMIN)
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()

    providers = client.get("/api/v1/providers").json()
    assert [item["key"] for item in providers] == ["tiktok", "scrapecreators", "apify"]
    assert not any(item["enabled"] for item in providers)

    no_key = client.put("/api/v1/providers/scrapecreators", json={"enabled": True})
    assert no_key.status_code == 422
    saved = client.put(
        "/api/v1/providers/scrapecreators",
        json={"credentials": {"api_key": "secret-value"}, "monthly_quota": 100},
    )
    assert saved.status_code == 200
    assert saved.json()["is_configured"] is True
    assert "secret-value" not in saved.text
    assert client.put("/api/v1/providers/unknown", json={}).status_code == 404
    assert client.put("/api/v1/providers/mock", json={}).status_code == 404

    no_source = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    )
    assert no_source.status_code == 409
    assert client.put("/api/v1/providers/scrapecreators", json={"enabled": True}).status_code == 200
    channel = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    ).json()
    sync_url = f"/api/v1/channels/{channel['id']}/sync"

    client.put("/api/v1/providers/scrapecreators", json={"enabled": False})
    assert client.post(sync_url).status_code == 409
    client.put("/api/v1/providers/scrapecreators", json={"enabled": True})

    run = client.post(sync_url)
    assert run.status_code == 200, run.text
    body = run.json()
    assert (body["status"], body["source"], body["handle"]) == (
        "success",
        "scrapecreators",
        "alpha.vn",
    )
    assert body["items_fetched"] == 2
    usage = {
        item["key"]: item["used_this_month"] for item in client.get("/api/v1/providers").json()
    }
    assert usage["scrapecreators"] == 2
    assert client.post("/api/v1/channels/missing/sync").status_code == 404

    runs = client.get("/api/v1/sync/runs", params={"limit": 10}).json()
    assert [(item["handle"], item["status"]) for item in runs] == [("alpha.vn", "success")] * 2
    assert client.get("/api/v1/sync/runs", params={"status": "failed"}).json() == []
    schedules = client.get("/api/v1/sync/schedules").json()
    assert schedules[0]["handle"] == "alpha.vn"
    assert schedules[0]["is_default_cron"] is True
    assert schedules[0]["next_run_at"] is not None

    token = client.put(
        f"/api/v1/channels/{channel['id']}/credential",
        json={"access_token": "tok", "expires_at": "2099-01-01T00:00:00Z"},
    )
    assert token.status_code == 200
    assert token.json()["connection_mode"] == "authorized"


def test_viewer_cannot_sync_or_edit_providers(client: TestClient) -> None:
    _login(client, **ADMIN)
    client.post(
        "/api/v1/users",
        json={"email": "v@example.com", "password": "password123", "role": "viewer"},
    )
    client.post("/api/v1/auth/logout")
    _login(client, "v@example.com", "password123")
    assert client.get("/api/v1/providers").status_code == 403
    assert client.get("/api/v1/sync/runs").status_code == 403
    assert (
        client.put("/api/v1/providers/scrapecreators", json={"enabled": False}).status_code == 403
    )
    assert client.post("/api/v1/channels/any/sync").status_code == 403


def test_metrics_and_videos_endpoints(client: TestClient) -> None:
    _login(client, **ADMIN)
    _enable_scrapecreators(client)
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    channel = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    ).json()

    metrics = client.get(f"/api/v1/channels/{channel['id']}/metrics?range=7d")
    assert metrics.status_code == 200, metrics.text
    assert metrics.json()["days"] == 7
    assert metrics.json()["current"]["follower_growth"] == 0
    videos = client.get(f"/api/v1/videos?channel_id={channel['id']}&range=7d")
    assert videos.status_code == 200
    assert videos.json() == []
    assert client.get(f"/api/v1/channels/{channel['id']}/metrics?range=abc").status_code == 422
    assert client.get("/api/v1/channels/missing/metrics").status_code == 404


def test_channel_history_start_is_validated(client: TestClient) -> None:
    _login(client, **ADMIN)
    _enable_scrapecreators(client)
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    body = {"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"}
    future = client.post("/api/v1/channels", json={**body, "history_since": "2099-01-01"})
    assert future.status_code == 422
    assert (
        client.post("/api/v1/channels", json={**body, "history_since": "nope"}).status_code == 422
    )
    created = client.post("/api/v1/channels", json={**body, "history_since": "2020-01-01"})
    assert created.status_code == 201, created.text


def test_overview_trend_and_filtered_video_endpoints(client: TestClient) -> None:
    _login(client, **ADMIN)
    _enable_scrapecreators(client)
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    channel = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    ).json()
    assert client.post(f"/api/v1/channels/{channel['id']}/sync").status_code == 200

    overview = client.get("/api/v1/analytics/overview?range=30d").json()
    assert overview["channel_count"] == 1
    assert overview["followers"] == 1200
    assert overview["channels"][0]["followers"] == 1200
    trend = client.get(f"/api/v1/channels/{channel['id']}/trend?range=7d").json()
    assert [point["followers"] for point in trend] == [1200]
    assert client.get("/api/v1/videos?sort=views&order=asc&q=zzz").json() == []
    runs = client.get(f"/api/v1/sync/runs?channel_id={channel['id']}").json()
    assert runs and all(run["channel_id"] == channel["id"] for run in runs)
    assert client.get("/api/v1/sync/runs?channel_id=missing").json() == []
    assert client.get("/api/v1/videos?sort=nope").status_code == 422
    activity = client.get(f"/api/v1/channels/{channel['id']}/posting-activity?range=365d")
    assert activity.status_code == 200, activity.text
    assert all(set(item) == {"day", "count"} and item["count"] > 0 for item in activity.json())
    assert client.get("/api/v1/channels/missing/posting-activity").status_code == 404
    paged = client.get("/api/v1/videos?limit=1&offset=0")
    assert paged.status_code == 200
    assert paged.headers["X-Total-Count"] == str(len(client.get("/api/v1/videos").json()))
    assert len(paged.json()) <= 1
    assert client.get("/api/v1/videos?offset=-1").status_code == 422


def test_compare_endpoint(client: TestClient) -> None:
    _login(client, **ADMIN)
    _enable_scrapecreators(client)
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    ids = [
        client.post(
            "/api/v1/channels",
            json={"partner_id": partner["id"], "handle": handle, "provider": "scrapecreators"},
        ).json()["id"]
        for handle in ("alpha.vn", "beta.vn")
    ]

    ok = client.get(f"/api/v1/analytics/compare?channel_ids={','.join(ids)}&range=7d")
    assert ok.status_code == 200, ok.text
    assert [item["channel_id"] for item in ok.json()["channels"]] == ids
    assert (
        client.get(f"/api/v1/analytics/compare?channel_ids={ids[0]},missing&range=7d").status_code
        == 404
    )
    too_many = ",".join(f"c{n}" for n in range(6))
    assert (
        client.get(f"/api/v1/analytics/compare?channel_ids={too_many}&range=7d").status_code == 422
    )


def test_daily_views_and_video_growth_endpoints(client: TestClient) -> None:
    _login(client, **ADMIN)
    _enable_scrapecreators(client)
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    channel = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    ).json()

    daily = client.get(f"/api/v1/channels/{channel['id']}/daily-views?range=7d")
    assert daily.status_code == 200, daily.text
    assert len(daily.json()) == 7
    growth = client.get(f"/api/v1/channels/{channel['id']}/video-growth?range=7d")
    assert growth.status_code == 200, growth.text
    assert client.get("/api/v1/channels/missing/daily-views").status_code == 404


def test_report_export_endpoint(client: TestClient) -> None:
    assert client.get("/api/v1/reports/export").status_code == 401
    _login(client, **ADMIN)
    _enable_scrapecreators(client)
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    )

    response = client.get("/api/v1/reports/export?kind=channels&range=7d")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert "alpha.vn" in response.text
    assert client.get("/api/v1/reports/export?partner_id=missing").status_code == 404


def test_notifications_endpoints(client: TestClient) -> None:
    assert client.get("/api/v1/notifications").status_code == 401
    _login(client, **ADMIN)

    listing = client.get("/api/v1/notifications")
    assert listing.status_code == 200, listing.text
    assert listing.json() == {"items": [], "unread_count": 0}
    assert client.post("/api/v1/notifications/read-all").json() == {"updated": 0}
    assert client.post("/api/v1/notifications/missing/read").status_code == 404


def test_period_variants(client: TestClient) -> None:
    _login(client, **ADMIN)
    for query in ("range=all", "range=1d", "date_from=2026-01-01&date_to=2026-01-31&tz_offset=420"):
        assert client.get(f"/api/v1/analytics/overview?{query}").status_code == 200
    assert client.get("/api/v1/analytics/overview?date_from=2026-01-01").status_code == 422
    assert client.get("/api/v1/analytics/overview?range=0d").status_code == 422
