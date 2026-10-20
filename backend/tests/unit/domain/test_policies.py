import pytest

from vinichannels.domain.channels.value_objects import ChannelStatus
from vinichannels.domain.syncing.entities import SyncStatus
from vinichannels.domain.syncing.policies import (
    FastPollPolicy,
    RetryPolicy,
    SyncErrorKind,
    has_consecutive_failures,
)


@pytest.mark.parametrize(
    ("kind", "transient"),
    [
        (SyncErrorKind.NETWORK, True),
        (SyncErrorKind.RATE_LIMITED, True),
        (SyncErrorKind.SERVER_ERROR, True),
        (SyncErrorKind.TOKEN_REVOKED, False),
        (SyncErrorKind.NOT_FOUND, False),
        (SyncErrorKind.PRIVATE, False),
    ],
)
def test_transient_classification(kind: SyncErrorKind, transient: bool) -> None:
    assert kind.is_transient is transient


def test_permanent_errors_map_to_channel_status() -> None:
    assert SyncErrorKind.TOKEN_REVOKED.resulting_channel_status is ChannelStatus.TOKEN_REVOKED
    assert SyncErrorKind.NOT_FOUND.resulting_channel_status is ChannelStatus.NOT_FOUND
    assert SyncErrorKind.PRIVATE.resulting_channel_status is ChannelStatus.PRIVATE
    assert SyncErrorKind.NETWORK.resulting_channel_status is None


def test_retry_only_transient_and_within_limit() -> None:
    policy = RetryPolicy(max_attempts=3)
    assert policy.should_retry(1, SyncErrorKind.NETWORK)
    assert policy.should_retry(2, SyncErrorKind.RATE_LIMITED)
    assert not policy.should_retry(3, SyncErrorKind.NETWORK)
    assert not policy.should_retry(1, SyncErrorKind.TOKEN_REVOKED)


def test_backoff_is_exponential_and_capped() -> None:
    policy = RetryPolicy(base_delay_sec=30, factor=2, max_delay_sec=100)
    assert policy.delay_for(0) == 0
    assert policy.delay_for(1) == 30
    assert policy.delay_for(2) == 60
    assert policy.delay_for(3) == 100


@pytest.mark.parametrize(
    ("age", "expected"),
    [(-1, None), (0, 15), (5.9, 15), (6, 60), (23.9, 60), (24, 180), (71.9, 180), (72, None)],
)
def test_fast_poll_intervals(age: float, expected: int | None) -> None:
    assert FastPollPolicy().interval_minutes(age) == expected


def test_consecutive_failures() -> None:
    failed, ok = SyncStatus.FAILED, SyncStatus.SUCCESS
    assert has_consecutive_failures([ok, failed, failed, failed])
    assert not has_consecutive_failures([failed, failed, ok, failed])
    assert not has_consecutive_failures([failed, failed])
    assert not has_consecutive_failures([failed], threshold=0)
