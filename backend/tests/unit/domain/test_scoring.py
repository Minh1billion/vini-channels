import pytest

from vinichannels.domain.analytics.scoring import (
    ScoreComponent,
    ScoreInputs,
    ScoreWeights,
    compute_scores,
    percentile_rank,
)
from vinichannels.domain.shared.errors import ValidationError


def test_default_weights_match_plan() -> None:
    weights = ScoreWeights()
    assert (weights.engagement, weights.growth, weights.reach, weights.consistency) == (
        0.40,
        0.25,
        0.20,
        0.15,
    )


def test_weights_must_sum_to_one_and_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        ScoreWeights(engagement=0.5, growth=0.5, reach=0.5, consistency=0.5)
    with pytest.raises(ValidationError):
        ScoreWeights(engagement=1.2, growth=-0.2, reach=0.0, consistency=0.0)


def test_percentile_rank_handles_ties_and_empty() -> None:
    population = [1.0, 2.0, 2.0, 3.0]
    assert percentile_rank(1.0, population) == pytest.approx(0.125)
    assert percentile_rank(2.0, population) == pytest.approx(0.5)
    assert percentile_rank(3.0, population) == pytest.approx(0.875)
    assert percentile_rank(1.0, []) is None


def test_best_channel_scores_highest() -> None:
    inputs = {
        "best": ScoreInputs(0.08, 0.10, 0.50, 7),
        "mid": ScoreInputs(0.05, 0.05, 0.30, 4),
        "worst": ScoreInputs(0.02, 0.00, 0.10, 1),
    }
    scores = compute_scores(inputs)
    best, mid, worst = (scores[key].total for key in ("best", "mid", "worst"))
    assert best is not None
    assert mid is not None
    assert worst is not None
    assert best > mid > worst
    assert 0 <= worst <= best <= 100


def test_scores_are_scale_independent() -> None:
    inputs = {
        "small": ScoreInputs(0.09, 0.2, 0.9, 5),
        "large": ScoreInputs(0.03, 0.01, 0.1, 5),
    }
    scores = compute_scores(inputs)
    assert scores["small"].total is not None
    assert scores["large"].total is not None
    assert scores["small"].total > scores["large"].total


def test_missing_component_reweights_remaining() -> None:
    inputs = {
        "a": ScoreInputs(erv=0.08),
        "b": ScoreInputs(erv=0.02),
    }
    scores = compute_scores(inputs)
    assert scores["a"].total == pytest.approx(75)
    assert scores["b"].total == pytest.approx(25)
    assert scores["a"].components[ScoreComponent.GROWTH] is None


def test_all_missing_gives_none() -> None:
    assert compute_scores({"a": ScoreInputs()})["a"].total is None


def test_custom_weights_change_the_ranking() -> None:
    inputs = {
        "engaged": ScoreInputs(0.09, 0.0, 0.1, 1),
        "growing": ScoreInputs(0.01, 0.3, 0.1, 1),
    }
    engagement_first = ScoreWeights(1.0, 0.0, 0.0, 0.0)
    growth_first = ScoreWeights(0.0, 1.0, 0.0, 0.0)
    a = compute_scores(inputs, engagement_first)
    b = compute_scores(inputs, growth_first)
    assert a["engaged"].total == pytest.approx(75)
    assert b["growing"].total == pytest.approx(75)
