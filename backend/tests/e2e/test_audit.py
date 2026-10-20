from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("argon2")

from fastapi.testclient import TestClient

from vinichannels.bootstrap.container import build_app
from vinichannels.bootstrap.settings import Settings

ADMIN = {"email": "admin@example.com", "password": "password123"}
API_KEY = "super-secret-api-key"
ACCESS_TOKEN = "super-secret-access-token"
REFRESH_TOKEN = "super-secret-refresh-token"


def _api(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/v1/tiktok/profile":
        return httpx.Response(
            200,
            json={
                "user": {"id": "1", "nickname": "Shop"},
                "stats": {
                    "followerCount": 10,
                    "followingCount": 1,
                    "heartCount": 1,
                    "videoCount": 0,
                },
            },
        )
    return httpx.Response(200, json={"aweme_list": [], "has_more": False})


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


def _login(client: TestClient, email: str, password: str) -> None:
    client.post("/api/v1/auth/logout")
    assert client.post("/api/v1/auth/login", json={"email": email, "password": password}).is_success


def test_changing_weights_writes_an_audit_entry(client: TestClient) -> None:
    _login(client, **ADMIN)
    client.put(
        "/api/v1/scoring/weights",
        json={"engagement": 0.5, "growth": 0.2, "reach": 0.2, "consistency": 0.1},
    )
    entries = client.get("/api/v1/audit", params={"action": "scoring.weights"}).json()
    assert len(entries) == 1
    assert entries[0]["actor_email"] == ADMIN["email"]
    assert entries[0]["detail"]["engagement"] == "0.4 → 0.5"
    today = datetime.now(UTC).date()
    window = {"date_from": str(today), "date_to": str(today)}
    assert len(client.get("/api/v1/audit", params=window).json()) >= 1
    past = {"date_to": str(today - timedelta(days=1))}
    assert client.get("/api/v1/audit", params=past).json() == []


def test_analyst_cannot_read_audit(client: TestClient) -> None:
    _login(client, **ADMIN)
    client.post(
        "/api/v1/users",
        json={"email": "a@example.com", "password": "password123", "role": "analyst"},
    )
    _login(client, "a@example.com", "password123")
    assert client.get("/api/v1/audit").status_code == 403


def test_entries_never_contain_keys_or_tokens(client: TestClient) -> None:
    _login(client, **ADMIN)
    client.put(
        "/api/v1/providers/scrapecreators",
        json={"credentials": {"api_key": API_KEY}, "enabled": True},
    )
    partner = client.post("/api/v1/partners", json={"name": "Alpha"}).json()
    expires = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    channel = client.post(
        "/api/v1/channels",
        json={"partner_id": partner["id"], "handle": "alpha.vn", "provider": "scrapecreators"},
    ).json()
    client.put(
        f"/api/v1/channels/{channel['id']}/credential",
        json={"access_token": ACCESS_TOKEN, "refresh_token": REFRESH_TOKEN, "expires_at": expires},
    )
    response = client.get("/api/v1/audit")
    actions = {item["action"] for item in response.json()}
    assert {"provider.update", "partner.create", "channel.register", "channel.token"} <= actions
    for secret in (API_KEY, ACCESS_TOKEN, REFRESH_TOKEN):
        assert secret not in response.text
