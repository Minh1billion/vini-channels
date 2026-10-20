import csv
import io
from dataclasses import dataclass
from enum import StrEnum

from vinichannels.application.authorization import require
from vinichannels.application.dto import VideoDTO
from vinichannels.application.errors import NotFound
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.analytics.metrics import (
    _video_dto,
    collect_period,
    metrics_for,
)
from vinichannels.application.use_cases.analytics.period import resolve_period
from vinichannels.application.use_cases.scoring.scoring import GetScoreboard
from vinichannels.domain.analytics.periods import PeriodSpec
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.ids import PartnerId

TOP_VIDEOS = 20
BOM = "﻿"

CHANNEL_COLUMNS = [
    "rank",
    "partner",
    "handle",
    "display_name",
    "score",
    "engagement_score",
    "growth_score",
    "reach_score",
    "consistency_score",
    "follower_growth",
    "follower_growth_ratio",
    "video_count",
    "total_views",
    "average_views",
    "erv",
    "posts_per_week",
]

VIDEO_COLUMNS = [
    "handle",
    "platform_video_id",
    "url",
    "caption",
    "posted_at",
    "views",
    "likes",
    "comments",
    "shares",
    "erv",
]


class ReportKind(StrEnum):
    CHANNELS = "channels"
    VIDEOS = "videos"


@dataclass(frozen=True, slots=True)
class ReportFile:
    filename: str
    content: str


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if not isinstance(value, str):
        return str(value)
    return f"'{value}" if value[:1] in ("=", "+", "-", "@") else value


def _render(columns: list[str], rows: list[list[object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_cell(value) for value in row])
    return BOM + buffer.getvalue()


class ExportReport:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, clock: Clock, scoreboard: GetScoreboard
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._scoreboard = scoreboard

    async def execute(
        self, actor: User, kind: ReportKind, spec: PeriodSpec, partner_id: str | None = None
    ) -> ReportFile:
        require(actor, Permission.REPORTS_EXPORT)
        async with self._uow_factory() as uow:
            period = await resolve_period(uow, self._clock, spec)
            if partner_id is not None and await uow.partners.get(PartnerId(partner_id)) is None:
                raise NotFound("Không tìm thấy đối tác")
            channels = await uow.channels.list_all(PartnerId(partner_id) if partner_id else None)
            data = {c.id: await collect_period(uow, c.id, period) for c in channels}
        name = f"report-{kind.value}-{period.start}-{period.end}.csv"
        if kind is ReportKind.VIDEOS:
            videos = [
                _video_dto(c.handle.value, v, s) for c in channels for v, s in data[c.id].videos
            ]
            return ReportFile(name, _videos_csv(videos))
        board = await self._scoreboard.compute(spec)
        scores = {item.channel_id: item for item in board.channels}
        rows: list[list[object]] = []
        for channel in sorted(
            channels, key=lambda c: (scores[c.id].rank is None, scores[c.id].rank or 0)
        ):
            score = scores[channel.id]
            metrics = metrics_for(period, data[channel.id])
            rows.append(
                [
                    score.rank,
                    score.partner_name,
                    score.handle,
                    score.display_name,
                    score.total,
                    score.components.get("engagement"),
                    score.components.get("growth"),
                    score.components.get("reach"),
                    score.components.get("consistency"),
                    metrics.follower_growth,
                    metrics.follower_growth_ratio,
                    metrics.video_count,
                    metrics.total_views,
                    metrics.average_views,
                    metrics.erv,
                    metrics.posts_per_week,
                ]
            )
        return ReportFile(name, _render(CHANNEL_COLUMNS, rows))


def _videos_csv(videos: list[VideoDTO]) -> str:
    top = sorted(videos, key=lambda v: v.views, reverse=True)[:TOP_VIDEOS]
    return _render(
        VIDEO_COLUMNS,
        [
            [
                v.handle,
                v.platform_video_id,
                v.url,
                v.caption,
                v.posted_at.isoformat(),
                v.views,
                v.likes,
                v.comments,
                v.shares,
                v.erv,
            ]
            for v in top
        ],
    )
