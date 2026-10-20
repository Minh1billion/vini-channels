from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta

import pytest

from vinichannels.domain.content.entities import Video
from vinichannels.domain.content.snapshots import ChannelSnapshot, VideoSnapshot
from vinichannels.domain.shared.errors import ValidationError
from vinichannels.domain.shared.ids import ChannelId, VideoId


def test_video_age_never_negative(now: datetime) -> None:
    video = Video(VideoId("v1"), ChannelId("c1"), "7000", posted_at=now - timedelta(hours=5))
    assert video.age_hours(now) == pytest.approx(5)
    assert video.age_hours(now - timedelta(hours=10)) == 0


def test_video_validation(now: datetime) -> None:
    with pytest.raises(ValidationError):
        Video(VideoId("v1"), ChannelId("c1"), "", posted_at=now)
    with pytest.raises(ValidationError):
        Video(VideoId("v1"), ChannelId("c1"), "7", posted_at=now, duration_sec=-1)
    with pytest.raises(ValidationError):
        Video(VideoId("v1"), ChannelId("c1"), "7", posted_at=datetime(2026, 1, 1))


def test_video_snapshot_engagements_and_validation(now: datetime) -> None:
    snapshot = VideoSnapshot(VideoId("v1"), now, "fake", views=1000, likes=50, comments=5, shares=3)
    assert snapshot.engagements == 58
    with pytest.raises(ValidationError):
        VideoSnapshot(VideoId("v1"), now, "fake", views=-1, likes=0, comments=0, shares=0)
    with pytest.raises(ValidationError):
        VideoSnapshot(VideoId("v1"), now, "fake", 1, 0, 0, 0, saves=-2)


def test_channel_snapshot_rejects_negative(now: datetime) -> None:
    ChannelSnapshot(ChannelId("c1"), now, "fake", followers=0)
    with pytest.raises(ValidationError):
        ChannelSnapshot(ChannelId("c1"), now, "fake", followers=-1)
    with pytest.raises(ValidationError):
        ChannelSnapshot(ChannelId("c1"), datetime(2026, 1, 1, tzinfo=None), "fake", followers=1)


def test_snapshots_are_immutable(now: datetime) -> None:
    snapshot = ChannelSnapshot(ChannelId("c1"), now.astimezone(UTC), "fake", followers=10)
    with pytest.raises(FrozenInstanceError):
        snapshot.followers = 20
