from dataclasses import dataclass
from datetime import datetime

from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import ChannelId, VideoId
from vinichannels.domain.shared.time import require_aware


@dataclass(slots=True)
class Video:
    id: VideoId
    channel_id: ChannelId
    platform_video_id: str
    posted_at: datetime
    url: str | None = None
    caption: str = ""
    thumbnail_url: str | None = None
    duration_sec: int = 0

    def __post_init__(self) -> None:
        require_aware(self.posted_at, "posted_at")
        if not self.platform_video_id:
            raise ValidationError("Mã video của nền tảng không được để trống")
        if self.duration_sec < 0:
            raise ValidationError("Thời lượng video không được âm")

    def age_hours(self, now: datetime) -> float:
        return max(0.0, (now - self.posted_at).total_seconds() / 3600)
