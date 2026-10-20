from dataclasses import dataclass
from datetime import datetime

from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import ChannelId, VideoId
from vinichannels.domain.shared.time import require_aware


def _non_negative(**values: int | None) -> None:
    for name, value in values.items():
        if value is not None and value < 0:
            raise ValidationError(f"{name} không được âm")


@dataclass(frozen=True, slots=True)
class ChannelSnapshot:
    channel_id: ChannelId
    captured_at: datetime
    source: str
    followers: int
    following: int = 0
    total_likes: int = 0
    video_count: int = 0

    def __post_init__(self) -> None:
        require_aware(self.captured_at, "captured_at")
        _non_negative(
            followers=self.followers,
            following=self.following,
            total_likes=self.total_likes,
            video_count=self.video_count,
        )


@dataclass(frozen=True, slots=True)
class VideoSnapshot:
    video_id: VideoId
    captured_at: datetime
    source: str
    views: int
    likes: int
    comments: int
    shares: int
    saves: int | None = None

    def __post_init__(self) -> None:
        require_aware(self.captured_at, "captured_at")
        _non_negative(
            views=self.views,
            likes=self.likes,
            comments=self.comments,
            shares=self.shares,
            saves=self.saves,
        )

    @property
    def engagements(self) -> int:
        return self.likes + self.comments + self.shares
