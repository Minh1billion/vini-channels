import asyncio
import io
import logging
from typing import Any

import httpx
from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import HTTPError as Urllib3Error

from vinichannels.application.ports.thumbnails import (
    StoredImage,
    is_valid_video_id,
    thumbnail_url,
)

log = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 5 * 1024 * 1024
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"heim", b"heis"}


def _sniff(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[4:8] == b"ftyp" and data[8:12] in _HEIF_BRANDS:
        return "image/heic"
    return None


def _heic_to_jpeg(data: bytes) -> bytes:
    # Trình duyệt (Chrome/Edge) không hiển thị được HEIC nên đổi sang JPEG.
    from PIL import Image
    from pillow_heif import register_heif_opener

    register_heif_opener()
    with Image.open(io.BytesIO(data)) as image:
        out = io.BytesIO()
        image.convert("RGB").save(out, format="JPEG", quality=85)
    return out.getvalue()


def normalize_image(data: bytes) -> tuple[bytes, str] | None:
    """Trả về (nội dung, content-type) dùng được trên trình duyệt, hoặc None nếu không phải ảnh."""
    kind = _sniff(data)
    if kind is None:
        return None
    if kind == "image/heic":
        return _heic_to_jpeg(data), "image/jpeg"
    return data, kind


class MinioThumbnailStore:
    def __init__(
        self,
        client: Minio,
        http_client: httpx.AsyncClient,
        bucket: str,
        max_bytes: int = MAX_IMAGE_BYTES,
    ) -> None:
        self._client = client
        self._http = http_client
        self._bucket = bucket
        self._max_bytes = max_bytes
        self._ready = False
        self._lock = asyncio.Lock()

    @staticmethod
    def _object(video_id: str) -> str:
        return f"thumbnails/{video_id}"

    async def mirror(self, platform_video_id: str, source_url: str) -> str | None:
        if not is_valid_video_id(platform_video_id) or not source_url.startswith(
            ("http://", "https://")
        ):
            return None
        name = self._object(platform_video_id)
        try:
            await self._ensure_bucket()
            if await asyncio.to_thread(self._exists, name):
                return thumbnail_url(platform_video_id)
            raw = await self._download(source_url)
            image = await asyncio.to_thread(normalize_image, raw) if raw else None
            if image is None:
                log.warning("Ảnh bìa %s không tải/đọc được từ %s", platform_video_id, source_url)
                return None
            await asyncio.to_thread(self._put, name, image[0], image[1])
        except (httpx.HTTPError, Urllib3Error, S3Error, OSError, ValueError) as error:
            log.warning("Không lưu được ảnh bìa %s: %s", platform_video_id, error)
            return None
        return thumbnail_url(platform_video_id)

    async def load(self, platform_video_id: str) -> StoredImage | None:
        if not is_valid_video_id(platform_video_id):
            return None
        try:
            return await asyncio.to_thread(self._read, self._object(platform_video_id))
        except S3Error as error:
            if error.code not in {"NoSuchKey", "NoSuchBucket"}:
                log.warning("Không đọc được ảnh bìa %s: %s", platform_video_id, error)
            return None
        except Urllib3Error as error:
            log.warning("Không kết nối được kho ảnh: %s", error)
            return None

    async def _download(self, url: str) -> bytes | None:
        response = await self._http.get(
            url,
            headers={"User-Agent": _USER_AGENT, "Accept": "image/*,*/*;q=0.8"},
            follow_redirects=True,
        )
        if response.status_code != 200:
            log.warning("Tải ảnh bìa lỗi HTTP %s: %s", response.status_code, url)
            return None
        if len(response.content) > self._max_bytes:
            return None
        return response.content

    async def _ensure_bucket(self) -> None:
        if self._ready:
            return
        async with self._lock:
            if self._ready:
                return
            await asyncio.to_thread(self._create_bucket)
            self._ready = True

    def _create_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            try:
                self._client.make_bucket(self._bucket)
            except S3Error as error:
                if error.code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                    raise

    def _exists(self, name: str) -> bool:
        try:
            self._client.stat_object(self._bucket, name)
        except S3Error as error:
            if error.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
                return False
            raise
        return True

    def _put(self, name: str, content: bytes, content_type: str) -> None:
        self._client.put_object(
            self._bucket, name, io.BytesIO(content), len(content), content_type=content_type
        )

    def _read(self, name: str) -> StoredImage:
        response: Any = self._client.get_object(self._bucket, name)
        try:
            content = response.read()
            content_type = response.headers.get("Content-Type", "application/octet-stream")
        finally:
            response.close()
            response.release_conn()
        return StoredImage(content=content, content_type=content_type)
