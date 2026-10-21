from vinichannels.application.ports.thumbnails import StoredImage


class DisabledThumbnailStore:
    """Dùng khi chưa cấu hình MinIO: giữ nguyên URL ảnh gốc của nhà cung cấp."""

    async def mirror(self, platform_video_id: str, source_url: str) -> str | None:
        return None

    async def load(self, platform_video_id: str) -> StoredImage | None:
        return None
