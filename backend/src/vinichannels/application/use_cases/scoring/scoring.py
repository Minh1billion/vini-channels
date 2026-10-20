from collections.abc import Callable, Sequence
from dataclasses import replace

from vinichannels.application.authorization import require
from vinichannels.application.dto import (
    ChannelScoreDTO,
    PartnerScoreDTO,
    ScoreboardDTO,
)
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.application.use_cases.analytics.metrics import collect_period, metrics_for
from vinichannels.application.use_cases.analytics.period import resolve_period
from vinichannels.application.use_cases.audit.recording import change, record
from vinichannels.domain.analytics.metrics import mean
from vinichannels.domain.analytics.periods import PeriodSpec
from vinichannels.domain.analytics.scoring import ScoreInputs, ScoreWeights, compute_scores
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.identity.entities import Permission, User


class GetScoringWeights:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, actor: User) -> ScoreWeights:
        require(actor, Permission.SCORING_READ)
        async with self._uow_factory() as uow:
            return await uow.scoring.get() or ScoreWeights()


class UpdateScoringWeights:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(
        self, actor: User, engagement: float, growth: float, reach: float, consistency: float
    ) -> ScoreWeights:
        require(actor, Permission.SCORING_WRITE)
        weights = ScoreWeights(engagement, growth, reach, consistency)
        async with self._uow_factory() as uow:
            previous = (await uow.scoring.get() or ScoreWeights()).as_dict()
            await uow.scoring.save(weights)
            changes = {
                name.value: change(previous[name], value)
                for name, value in weights.as_dict().items()
                if previous[name] != value
            }
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.SCORING_WEIGHTS,
                "scoring",
                "weights",
                "Trọng số điểm",
                changes,
            )
            await uow.commit()
        return weights


def _ranked[T](
    items: Sequence[T], total: Callable[[T], float | None], name: Callable[[T], str]
) -> list[T]:
    return sorted(
        items,
        key=lambda item: (total(item) is None, -(total(item) or 0.0), name(item).casefold()),
    )


class GetScoreboard:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, spec: PeriodSpec) -> ScoreboardDTO:
        require(actor, Permission.SCORING_READ)
        return await self.compute(spec)

    async def compute(self, spec: PeriodSpec) -> ScoreboardDTO:
        inputs: dict[str, ScoreInputs] = {}
        async with self._uow_factory() as uow:
            period = await resolve_period(uow, self._clock, spec)
            weights = await uow.scoring.get() or ScoreWeights()
            partners = {partner.id: partner for partner in await uow.partners.list_all()}
            channels = [c for c in await uow.channels.list_all() if c.partner_id in partners]
            for channel in channels:
                metrics = metrics_for(period, await collect_period(uow, channel.id, period))
                inputs[channel.id] = ScoreInputs(
                    erv=metrics.erv,
                    follower_growth_ratio=metrics.follower_growth_ratio,
                    reach_ratio=metrics.reach_ratio,
                    posts_per_week=metrics.posts_per_week,
                )
        scores = compute_scores(inputs, weights)

        unranked = [
            ChannelScoreDTO(
                channel_id=channel.id,
                partner_id=channel.partner_id,
                partner_name=partners[channel.partner_id].name,
                handle=channel.handle.value,
                display_name=channel.display_name,
                rank=None,
                total=scores[channel.id].total,
                components={k.value: v for k, v in scores[channel.id].components.items()},
                erv=inputs[channel.id].erv,
                follower_growth_ratio=inputs[channel.id].follower_growth_ratio,
                reach_ratio=inputs[channel.id].reach_ratio,
                posts_per_week=inputs[channel.id].posts_per_week,
            )
            for channel in channels
        ]
        ranked_channels = [
            _with_rank(item, index)
            for index, item in enumerate(
                _ranked(unranked, lambda i: i.total, lambda i: i.handle), start=1
            )
        ]

        partner_items: list[PartnerScoreDTO] = []
        for partner in partners.values():
            own = [item for item in ranked_channels if item.partner_id == partner.id]
            totals = [item.total for item in own if item.total is not None]
            partner_items.append(
                PartnerScoreDTO(
                    partner_id=partner.id,
                    name=partner.name,
                    rank=None,
                    total=mean(totals),
                    channel_count=len(own),
                    scored_channel_count=len(totals),
                )
            )
        ranked_partners = [
            _with_rank(item, index)
            for index, item in enumerate(
                _ranked(partner_items, lambda i: i.total, lambda i: i.name), start=1
            )
        ]
        return ScoreboardDTO(
            period_start=period.start,
            period_end=period.end,
            days=period.days,
            weights=weights,
            channels=ranked_channels,
            partners=ranked_partners,
        )


def _with_rank[T: (ChannelScoreDTO, PartnerScoreDTO)](item: T, position: int) -> T:
    return replace(item, rank=position if item.total is not None else None)
