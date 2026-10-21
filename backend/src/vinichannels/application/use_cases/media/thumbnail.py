from vinichannels.application.authorization import require
from vinichannels.application.errors import NotFound
from vinichannels.application.ports.thumbnails import StoredImage, ThumbnailStore, is_valid_video_id
from vinichannels.domain.identity.entities import Permission, User


class GetThumbnail:
    def __init__(self, store: ThumbnailStore) -> None:
        self._store = store

    async def execute(self, actor: User, platform_video_id: str) -> StoredImage:
        require(actor, Permission.ANALYTICS_READ)
        image = (
            await self._store.load(platform_video_id)
            if is_valid_video_id(platform_video_id)
            else None
        )
        if image is None:
            raise NotFound("Không tìm thấy ảnh bìa")
        return image
