import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from vinichannels.domain.shared.errors import ValidationError


class ScoreComponent(StrEnum):
    ENGAGEMENT = "engagement"
    GROWTH = "growth"
    REACH = "reach"
    CONSISTENCY = "consistency"


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    engagement: float = 0.40
    growth: float = 0.25
    reach: float = 0.20
    consistency: float = 0.15

    def __post_init__(self) -> None:
        values = self.as_dict().values()
        if any(v < 0 for v in values):
            raise ValidationError("Trọng số không được âm")
        if not math.isclose(sum(values), 1.0, abs_tol=1e-9):
            raise ValidationError("Tổng trọng số phải bằng 1")

    def as_dict(self) -> dict[ScoreComponent, float]:
        return {
            ScoreComponent.ENGAGEMENT: self.engagement,
            ScoreComponent.GROWTH: self.growth,
            ScoreComponent.REACH: self.reach,
            ScoreComponent.CONSISTENCY: self.consistency,
        }


@dataclass(frozen=True, slots=True)
class ScoreInputs:
    erv: float | None = None
    follower_growth_ratio: float | None = None
    reach_ratio: float | None = None
    posts_per_week: float | None = None

    def component_values(self) -> dict[ScoreComponent, float | None]:
        return {
            ScoreComponent.ENGAGEMENT: self.erv,
            ScoreComponent.GROWTH: self.follower_growth_ratio,
            ScoreComponent.REACH: self.reach_ratio,
            ScoreComponent.CONSISTENCY: self.posts_per_week,
        }


@dataclass(frozen=True, slots=True)
class PerformanceScore:
    total: float | None
    components: dict[ScoreComponent, float | None]


def percentile_rank(value: float, population: Sequence[float]) -> float | None:
    if not population:
        return None
    below = sum(1 for item in population if item < value)
    equal = sum(1 for item in population if item == value)
    return (below + 0.5 * equal) / len(population)


def compute_scores(
    inputs: Mapping[str, ScoreInputs], weights: ScoreWeights | None = None
) -> dict[str, PerformanceScore]:
    active = weights or ScoreWeights()
    weight_map = active.as_dict()
    populations: dict[ScoreComponent, list[float]] = {component: [] for component in weight_map}
    for item in inputs.values():
        for component, value in item.component_values().items():
            if value is not None:
                populations[component].append(value)

    result: dict[str, PerformanceScore] = {}
    for key, item in inputs.items():
        ranks: dict[ScoreComponent, float | None] = {}
        weighted = 0.0
        used_weight = 0.0
        for component, value in item.component_values().items():
            rank = None if value is None else percentile_rank(value, populations[component])
            ranks[component] = None if rank is None else rank * 100
            if rank is not None and weight_map[component] > 0:
                weighted += weight_map[component] * rank
                used_weight += weight_map[component]
        total = None if used_weight == 0 else 100 * weighted / used_weight
        result[key] = PerformanceScore(total=total, components=ranks)
    return result
