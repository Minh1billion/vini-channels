import time
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

PROFILES = {
    "alpha.vn": {"followerCount": 10_000, "likes": 100},
    "beta.vn": {"followerCount": 100, "likes": 10},
}


def _api(request: httpx.Request) -> httpx.Response:
    profile = PROFILES[request.url.params["handle"]]
    if request.url.path == "/v1/tiktok/profile":
        return httpx.Response(
            200,
            json={
                "user": {"id": "1", "nickname": "Shop"},
                "stats": {
                    "followerCount": profile["followerCount"],
                    "followingCount": 5,
                    "heartCount": 900,
                    "videoCount": 2,
                },
            },
        )
    posted = int(time.time()) - 86_400
    return httpx.Response(
        200,
        json={
            "aweme_list": [
                {
                    "aweme_id": str(video_id),
                    "create_time": posted - video_id,
                    "video": {"duration": 15000},
                    "statistics": {
                        "play_count": 1000,
                        "digg_count": profile["likes"],
                        "comment_count": 0,
                        "share_count": 0,
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
    )
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(_api))
    with TestClient(build_app(settings, http_client)) as test_client:
        yield test_client


def _seed(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json=ADMIN)
    client.put(
        "/api/v1/providers/scrapecreators",
        json={"credentials": {"api_key": "secret-value"}, "enabled": True},
    )
    for name, handle in (("Alpha Co", "alpha.vn"), ("Beta Co", "beta.vn")):
        partner = client.post("/api/v1/partners", json={"name": name}).json()
        created = client.post(
            "/api/v1/channels",
            json={"partner_id": partner["id"], "handle": handle, "provider": "scrapecreators"},
        )
        assert created.status_code == 201, created.text


def _totals(client: TestClient) -> dict[str, float]:
    body = client.get("/api/v1/scoring?range=30d").json()
    return {item["handle"]: item["total"] for item in body["channels"]}


def test_changing_weights_changes_scores_and_ranking(client: TestClient) -> None:
    _seed(client)
    assert client.get("/api/v1/scoring/weights").json()["engagement"] == 0.4
    before = client.get("/api/v1/scoring?range=30d").json()
    assert [item["name"] for item in before["partners"]] == ["Alpha Co", "Beta Co"]
    assert [item["rank"] for item in before["channels"]] == [1, 2]
    totals_before = _totals(client)
    assert totals_before["alpha.vn"] > totals_before["beta.vn"]

    updated = client.put(
        "/api/v1/scoring/weights",
        json={"engagement": 0, "growth": 0, "reach": 1, "consistency": 0},
    )
    assert updated.status_code == 200, updated.text

    after = client.get("/api/v1/scoring?range=30d").json()
    assert after["weights"]["reach"] == 1
    assert [item["name"] for item in after["partners"]] == ["Beta Co", "Alpha Co"]
    assert [item["handle"] for item in after["channels"]] == ["beta.vn", "alpha.vn"]
    totals_after = _totals(client)
    assert totals_after["beta.vn"] == pytest.approx(75)
    assert totals_after["alpha.vn"] == pytest.approx(25)
    assert totals_after != totals_before


def test_weights_must_sum_to_one_and_need_permission(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json=ADMIN)
    invalid = client.put(
        "/api/v1/scoring/weights",
        json={"engagement": 0.5, "growth": 0.5, "reach": 0.5, "consistency": 0},
    )
    assert invalid.status_code == 422
    assert client.get("/api/v1/scoring/weights").json()["growth"] == 0.25
    client.post(
        "/api/v1/users",
        json={"email": "v@example.com", "password": "password123", "role": "viewer"},
    )
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/login", json={"email": "v@example.com", "password": "password123"})
    assert client.get("/api/v1/scoring").status_code == 403
    assert client.get("/api/v1/scoring/weights").status_code == 403
