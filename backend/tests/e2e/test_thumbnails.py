import time
from collections.abc import Iterator

import httpx
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("argon2")
pytest.importorskip("minio")

from fastapi.testclient import TestClient

from vinichannels.application.ports.thumbnails import StoredImage, thumbnail_url
from vinichannels.bootstrap.container import build_app
from vinichannels.bootstrap.settings import Settings

ADMIN = {"email": "admin@example.com", "password": "password123"}


def _scrapecreators_api(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/v1/tiktok/profile":
        return httpx.Response(
            200,
            json={
                "user": {"id": "1", "nickname": "Alpha", "avatarLarger": "http://a/a.png"},
                "stats": {
                    "followerCount": 10,
                    "followingCount": 1,
                    "heartCount": 9,
                    "videoCount": 1,
                },
            },
        )
    return httpx.Response(
        200,
        json={
            "aweme_list": [
                {
                    "aweme_id": "8001",
                    "desc": "video",
                    "create_time": 1_760_000_000,
                    "video": {
                        "duration": 15000,
                        "cover": {
                            "url_list": [
                                "https://p16.tiktokcdn-eu.com/a~q70.heic?dr=1",
                                "https://p16.tiktokcdn-eu.com/a~q70.jpeg?dr=1",
                            ]
                        },
                    },
                    "statistics": {
                        "play_count": 100,
                        "digg_count": 10,
                        "comment_count": 1,
                        "share_count": 2,
                    },
                }
            ],
            "has_more": False,
        },
    )


class _MemoryStore:
    def __init__(self) -> None:
        self.sources: list[str] = []
        self.images: dict[str, StoredImage] = {}

    async def mirror(self, platform_video_id: str, source_url: str) -> str | None:
        self.sources.append(source_url)
        self.images[platform_video_id] = StoredImage(b"\xff\xd8\xff-image", "image/jpeg")
        return thumbnail_url(platform_video_id)

    async def load(self, platform_video_id: str) -> StoredImage | None:
        return self.images.get(platform_video_id)


@pytest.fixture
def store() -> _MemoryStore:
    return _MemoryStore()


@pytest.fixture
def client(store: _MemoryStore) -> Iterator[TestClient]:
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        secret_key="test-secret-key-with-at-least-32-bytes!!",
        admin_email=ADMIN["email"],
        admin_password=ADMIN["password"],
        sync_lookback_days=0,
    )
    http_client = httpx.AsyncClient(transport=httpx.MockTransport(_scrapecreators_api))
    with TestClient(build_app(settings, http_client, thumbnail_store=store)) as test_client:
        yield test_client


def test_registered_channel_serves_mirrored_thumbnail(
    client: TestClient, store: _MemoryStore
) -> None:
    assert client.get("/api/v1/media/thumbnails/8001").status_code == 401
    client.post("/api/v1/auth/login", json=ADMIN)
    client.put(
        "/api/v1/providers/scrapecreators",
        json={"credentials": {"api_key": "secret-value"}, "enabled": True},
    )
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    created = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    )
    assert created.status_code == 201, created.text

    videos = client.get("/api/v1/videos", params={"range": "all"}).json()

    assert videos[0]["thumbnail_url"] == "/api/v1/media/thumbnails/8001"
    assert store.sources == ["https://p16.tiktokcdn-eu.com/a~q70.jpeg?dr=1"]
    image = client.get(videos[0]["thumbnail_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert image.content == b"\xff\xd8\xff-image"
    assert client.get("/api/v1/media/thumbnails/404404").status_code == 404


def _wait_for_job(client: TestClient) -> dict[str, object]:
    for _ in range(100):
        job = client.get("/api/v1/jobs").json()[0]
        if job["status"] != "running":
            return job  # type: ignore[no-any-return]
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_background_jobs_register_and_sync(client: TestClient) -> None:
    client.post("/api/v1/auth/login", json=ADMIN)
    client.put(
        "/api/v1/providers/scrapecreators",
        json={"credentials": {"api_key": "secret-value"}, "enabled": True},
    )
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    body = {"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"}

    started = client.post("/api/v1/jobs/channels", json=body)
    assert started.status_code == 202
    registered = _wait_for_job(client)
    assert registered["status"] == "success"
    assert registered["channel_id"]

    synced_start = client.post(f"/api/v1/jobs/channels/{registered['channel_id']}/sync")
    assert synced_start.status_code == 202
    synced = _wait_for_job(client)
    assert synced["kind"] == "sync"
    assert synced["status"] == "success"

    duplicate = client.post("/api/v1/jobs/channels", json=body)
    assert _wait_for_job(client)["status"] == "failed"
    assert duplicate.status_code == 202
