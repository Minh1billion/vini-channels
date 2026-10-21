import re
from dataclasses import dataclass
from typing import Protocol

# Đường dẫn công khai (tương đối) mà API phục vụ ảnh bìa đã lưu.
THUMBNAIL_PATH = "/api/v1/media/thumbnails"

_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def is_valid_video_id(video_id: str) -> bool:
    return _VIDEO_ID.fullmatch(video_id) is not None


def thumbnail_url(video_id: str) -> str:
    return f"{THUMBNAIL_PATH}/{video_id}"


@dataclass(frozen=True, slots=True)
class StoredImage:
    content: bytes
    content_type: str


class ThumbnailStore(Protocol):
    async def mirror(self, platform_video_id: str, source_url: str) -> str | None:
        """Tải ảnh từ source_url về kho lưu trữ.

        Trả về URL nội bộ nếu ảnh đã có hoặc vừa lưu xong, None nếu không lưu được
        (khi đó giữ nguyên URL gốc của nhà cung cấp).
        """
        ...

    async def load(self, platform_video_id: str) -> StoredImage | None: ...
