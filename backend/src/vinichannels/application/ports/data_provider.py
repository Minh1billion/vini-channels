from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from vinichannels.application.progress import Progress
from vinichannels.domain.syncing.policies import SyncErrorKind


class ProviderError(Exception):
    def __init__(self, kind: SyncErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


class ProviderUnavailable(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True, slots=True)
class FetchRequest:
    handle: str
    platform_channel_id: str | None
    credentials: Mapping[str, str]
    max_videos: int | None
    now: datetime
    since: datetime | None = None
    max_pages: int = 3
    progress: Progress | None = None


@dataclass(frozen=True, slots=True)
class FetchedProfile:
    platform_channel_id: str | None
    display_name: str | None
    avatar_url: str | None
    followers: int
    following: int = 0
    total_likes: int = 0
    video_count: int = 0


@dataclass(frozen=True, slots=True)
class FetchedVideo:
    platform_video_id: str
    posted_at: datetime
    views: int
    likes: int
    comments: int
    shares: int
    saves: int | None = None
    url: str | None = None
    caption: str = ""
    thumbnail_url: str | None = None
    duration_sec: int = 0


@dataclass(frozen=True, slots=True)
class ProviderData:
    profile: FetchedProfile
    videos: tuple[FetchedVideo, ...]
    warning: str | None = None


class DataProvider(Protocol):
    key: str

    async def fetch(self, request: FetchRequest) -> ProviderData: ...
