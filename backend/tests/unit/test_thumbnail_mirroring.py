import asyncio
import io
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

pytest.importorskip("minio")
pytest.importorskip("PIL")
pytest.importorskip("pillow_heif")

from minio.error import S3Error
from PIL import Image
from pillow_heif import register_heif_opener

from vinichannels.adapters.outbound.storage.minio_store import MinioThumbnailStore
from vinichannels.application.ports.data_provider import (
    FetchedProfile,
    FetchedVideo,
    ProviderData,
)
from vinichannels.application.ports.thumbnails import StoredImage
from vinichannels.application.use_cases.syncing.thumbnails import mirror_thumbnails

NOW = datetime(2026, 10, 21, tzinfo=UTC)


def _image(fmt: str) -> bytes:
    register_heif_opener()
    out = io.BytesIO()
    Image.new("RGB", (30, 40), (200, 30, 30)).save(out, format=fmt)
    return out.getvalue()


def _s3_error(code: str) -> S3Error:
    return S3Error(code, code, "res", "req", "host", None)  # type: ignore[arg-type]


class _Response:
    def __init__(self, content: bytes, content_type: str) -> None:
        self._content = content
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self._content

    def close(self) -> None: ...

    def release_conn(self) -> None: ...


class FakeMinio:
    def __init__(self) -> None:
        self.buckets: set[str] = set()
        self.objects: dict[str, tuple[bytes, str]] = {}

    def bucket_exists(self, bucket: str) -> bool:
        return bucket in self.buckets

    def make_bucket(self, bucket: str) -> None:
        self.buckets.add(bucket)

    def stat_object(self, bucket: str, name: str) -> None:
        if name not in self.objects:
            raise _s3_error("NoSuchKey")

    def put_object(
        self, bucket: str, name: str, data: io.BytesIO, length: int, content_type: str
    ) -> None:
        self.objects[name] = (data.read(), content_type)

    def get_object(self, bucket: str, name: str) -> _Response:
        if name not in self.objects:
            raise _s3_error("NoSuchKey")
        return _Response(*self.objects[name])


def _store(
    handler: Any, minio: FakeMinio, **kwargs: Any
) -> tuple[MinioThumbnailStore, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(record))
    return MinioThumbnailStore(minio, http, "thumbs", **kwargs), seen  # type: ignore[arg-type]


def test_mirror_saves_jpeg_and_creates_bucket() -> None:
    jpeg = _image("JPEG")
    minio = FakeMinio()
    store, seen = _store(lambda _: httpx.Response(200, content=jpeg), minio)

    url = asyncio.run(store.mirror("7001", "https://cdn.example/a.jpeg"))

    assert url == "/api/v1/media/thumbnails/7001"
    assert "thumbs" in minio.buckets
    assert minio.objects["thumbnails/7001"] == (jpeg, "image/jpeg")
    assert seen[0].headers["User-Agent"].startswith("Mozilla/")


def test_mirror_converts_heic_to_jpeg_for_browsers() -> None:
    heic = _image("HEIF")
    minio = FakeMinio()
    store, _ = _store(lambda _: httpx.Response(200, content=heic), minio)

    assert asyncio.run(store.mirror("7002", "https://cdn.example/a.heic")) is not None

    content, content_type = minio.objects["thumbnails/7002"]
    assert content_type == "image/jpeg"
    assert content.startswith(b"\xff\xd8\xff")


def test_mirror_skips_download_when_already_stored() -> None:
    minio = FakeMinio()
    minio.buckets.add("thumbs")
    minio.objects["thumbnails/7003"] = (b"old", "image/jpeg")
    store, seen = _store(lambda _: httpx.Response(500), minio)

    assert asyncio.run(store.mirror("7003", "https://cdn.example/a.jpeg")) is not None
    assert seen == []


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(403, text="Access Denied"),
        httpx.Response(200, content=b"<html>not an image</html>"),
        httpx.Response(200, content=b"\xff\xd8\xff" + b"0" * 100),
    ],
)
def test_mirror_returns_none_when_image_is_unusable(response: httpx.Response) -> None:
    minio = FakeMinio()
    store, _ = _store(lambda _: response, minio, max_bytes=50)

    assert asyncio.run(store.mirror("7004", "https://cdn.example/a.jpeg")) is None
    assert minio.objects == {}


def test_mirror_rejects_bad_ids_and_non_http_urls() -> None:
    store, seen = _store(lambda _: httpx.Response(200, content=_image("JPEG")), FakeMinio())

    assert asyncio.run(store.mirror("../etc", "https://cdn.example/a.jpeg")) is None
    assert asyncio.run(store.mirror("7005", "file:///etc/passwd")) is None
    assert seen == []


def test_load_returns_stored_image_or_none() -> None:
    minio = FakeMinio()
    minio.objects["thumbnails/7006"] = (b"img", "image/png")
    store, _ = _store(lambda _: httpx.Response(500), minio)

    assert asyncio.run(store.load("7006")) == StoredImage(b"img", "image/png")
    assert asyncio.run(store.load("9999")) is None
    assert asyncio.run(store.load("../x")) is None


class _FakeStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def mirror(self, platform_video_id: str, source_url: str) -> str | None:
        self.calls.append((platform_video_id, source_url))
        if platform_video_id == "bad":
            return None
        return f"/api/v1/media/thumbnails/{platform_video_id}"

    async def load(self, platform_video_id: str) -> StoredImage | None:
        return None


def _video(video_id: str, thumb: str | None) -> FetchedVideo:
    return FetchedVideo(
        platform_video_id=video_id,
        posted_at=NOW,
        views=1,
        likes=0,
        comments=0,
        shares=0,
        thumbnail_url=thumb,
    )


def test_mirror_thumbnails_rewrites_only_what_was_saved() -> None:
    data = ProviderData(
        profile=FetchedProfile(None, None, None, 0),
        videos=(
            _video("1", "https://cdn/1.jpeg"),
            _video("bad", "https://cdn/bad.jpeg"),
            _video("3", None),
            _video("4", "/api/v1/media/thumbnails/4"),
        ),
    )
    store = _FakeStore()

    result = asyncio.run(mirror_thumbnails(store, data))

    assert [v.thumbnail_url for v in result.videos] == [
        "/api/v1/media/thumbnails/1",
        "https://cdn/bad.jpeg",
        None,
        "/api/v1/media/thumbnails/4",
    ]
    assert [call[0] for call in store.calls] == ["1", "bad"]


def test_mirror_thumbnails_is_noop_without_store() -> None:
    data = ProviderData(profile=FetchedProfile(None, None, None, 0), videos=(_video("1", "https://cdn/1.jpeg"),))

    assert asyncio.run(mirror_thumbnails(None, data)) is data


def test_scrapecreators_prefers_non_heic_cover() -> None:
    from vinichannels.adapters.outbound.providers.scrapecreators import _pick_cover

    assert _pick_cover(["https://a/x.heic?dr=1", "https://a/x.jpeg?dr=1"]) == "https://a/x.jpeg?dr=1"
    assert _pick_cover(["https://a/x.heic?dr=1"]) == "https://a/x.heic?dr=1"
    assert _pick_cover([]) is None


def test_mirror_and_load_survive_storage_being_down() -> None:
    from urllib3.exceptions import MaxRetryError

    class Down(FakeMinio):
        def bucket_exists(self, bucket: str) -> bool:
            raise MaxRetryError(None, "http://minio:9000")  # type: ignore[arg-type]

        def get_object(self, bucket: str, name: str) -> _Response:
            raise MaxRetryError(None, "http://minio:9000")  # type: ignore[arg-type]

    store, _ = _store(lambda _: httpx.Response(200, content=_image("JPEG")), Down())

    assert asyncio.run(store.mirror("7007", "https://cdn.example/a.jpeg")) is None
    assert asyncio.run(store.load("7007")) is None
