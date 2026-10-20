import csv
import io

import pytest

from tests.unit.application.conftest import World, add_channel, run
from tests.unit.application.test_analytics_use_cases import (
    LAST_7,
    at,
    seed_followers,
    seed_video,
)
from vinichannels.application.errors import NotFound, PermissionDenied
from vinichannels.application.use_cases.partners.crud import CreatePartner
from vinichannels.application.use_cases.reports.export import (
    CHANNEL_COLUMNS,
    VIDEO_COLUMNS,
    ExportReport,
    ReportKind,
)
from vinichannels.application.use_cases.scoring.scoring import GetScoreboard
from vinichannels.domain.identity.entities import Role, User


def _exporter(world: World) -> ExportReport:
    return ExportReport(world.uow, world.clock, GetScoreboard(world.uow, world.clock))


def _rows(text: str) -> list[dict[str, str]]:
    assert text.startswith("﻿")
    return list(csv.DictReader(io.StringIO(text.removeprefix("﻿"))))


@pytest.fixture
def channels(world: World, manager: User) -> tuple[str, str, str]:
    alpha = run(CreatePartner(world.uow, world.clock).execute(manager, "Alpha"))
    beta = run(CreatePartner(world.uow, world.clock).execute(manager, "Beta"))
    first = add_channel(world, alpha.id, "alpha").id
    second = add_channel(world, beta.id, "beta").id
    seed_followers(world, first, (at(13), 1000), (at(19, 6), 1100))
    seed_followers(world, second, (at(13), 200), (at(19, 6), 180))
    seed_video(world, first, "a", at(14), (at(18), 1000, 100))
    seed_video(world, second, "=b", at(15), (at(18), 400, 20))
    return first, alpha.id, second


def test_channels_csv_has_columns_and_values(
    world: World, manager: User, channels: tuple[str, str, str]
) -> None:
    report = run(_exporter(world).execute(manager, ReportKind.CHANNELS, LAST_7))

    header = report.content.removeprefix("﻿").splitlines()[0]
    assert header.split(",") == CHANNEL_COLUMNS
    rows = {row["handle"]: row for row in _rows(report.content)}
    assert set(rows) == {"alpha", "beta"}
    assert rows["alpha"]["partner"] == "Alpha"
    assert rows["alpha"]["follower_growth"] == "100"
    assert rows["alpha"]["total_views"] == "1000"
    assert float(rows["alpha"]["erv"]) == pytest.approx(0.1)
    assert rows["beta"]["follower_growth"] == "-20"
    assert rows["alpha"]["rank"] in {"1", "2"}
    assert rows["alpha"]["score"] != ""


def test_channels_csv_can_be_limited_to_partner(
    world: World, manager: User, channels: tuple[str, str, str]
) -> None:
    report = run(_exporter(world).execute(manager, ReportKind.CHANNELS, LAST_7, channels[1]))

    assert [row["handle"] for row in _rows(report.content)] == ["alpha"]


def test_videos_csv_lists_top_videos_and_escapes_formulas(
    world: World, manager: User, channels: tuple[str, str, str]
) -> None:
    report = run(_exporter(world).execute(manager, ReportKind.VIDEOS, LAST_7))

    assert report.content.removeprefix("﻿").splitlines()[0].split(",") == VIDEO_COLUMNS
    rows = _rows(report.content)
    assert [row["platform_video_id"] for row in rows] == ["a", "'=b"]
    assert (rows[0]["views"], rows[0]["likes"]) == ("1000", "100")
    assert float(rows[0]["erv"]) == pytest.approx(0.1)


def test_export_requires_permission_and_known_partner(
    world: World, manager: User, channels: tuple[str, str, str]
) -> None:
    blocked = world.user(Role.VIEWER)
    blocked.is_active = False

    with pytest.raises(PermissionDenied):
        run(_exporter(world).execute(blocked, ReportKind.CHANNELS, LAST_7))
    with pytest.raises(NotFound):
        run(_exporter(world).execute(manager, ReportKind.CHANNELS, LAST_7, "missing"))
