import pytest

from tests.unit.application.conftest import World, add_channel, run
from vinichannels.application.use_cases.search.global_search import GlobalSearch
from vinichannels.domain.content.entities import Video
from vinichannels.domain.identity.entities import ROLE_PERMISSIONS, Permission, Role, User
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.shared.ids import ChannelId, PartnerId, VideoId, new_id


def seed(world: World) -> tuple[Partner, str]:
    partner = Partner(id=PartnerId(new_id()), name="Alpha Media")
    world.uow.state.partners[partner.id] = partner
    channel = add_channel(world, partner.id, "alphashop")
    video = Video(
        id=VideoId(new_id()),
        channel_id=ChannelId(channel.id),
        platform_video_id="v1",
        posted_at=world.clock.now(),
        caption="Alpha unboxing",
    )
    world.uow.state.videos[video.id] = video
    return partner, channel.id


def test_search_finds_partners_channels_and_videos(world: World, viewer: User) -> None:
    seed(world)
    result = run(GlobalSearch(world.uow).execute(viewer, " alpha "))
    assert [p.name for p in result.partners] == ["Alpha Media"]
    assert [c.handle for c in result.channels] == ["alphashop"]
    assert [v.caption for v in result.videos] == ["Alpha unboxing"]
    assert run(GlobalSearch(world.uow).execute(viewer, "a")).partners == []


def test_search_respects_permissions_and_archive(
    world: World, viewer: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    partner, _ = seed(world)
    search = GlobalSearch(world.uow)
    monkeypatch.setitem(ROLE_PERMISSIONS, Role.VIEWER, frozenset({Permission.PARTNERS_READ}))
    limited = run(search.execute(viewer, "alpha"))
    assert limited.partners and limited.channels and limited.videos == []
    monkeypatch.setitem(ROLE_PERMISSIONS, Role.VIEWER, frozenset({Permission.ANALYTICS_READ}))
    only_videos = run(search.execute(viewer, "alpha"))
    assert only_videos.partners == [] and only_videos.channels == [] and only_videos.videos
    monkeypatch.undo()
    viewer.is_active = False
    empty = run(search.execute(viewer, "alpha"))
    assert (empty.partners, empty.channels, empty.videos) == ([], [], [])
    viewer.is_active = True
    partner.archive(world.clock.now())
    for channel in world.uow.state.channels.values():
        channel.archive(world.clock.now())
    hidden = run(search.execute(viewer, "alpha"))
    assert (hidden.partners, hidden.channels, hidden.videos) == ([], [], [])
