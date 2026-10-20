from vinichannels.application.authorization import require
from vinichannels.application.dto import ChannelMetricsDTO
from vinichannels.application.use_cases.analytics.metrics import GetChannelMetrics
from vinichannels.domain.analytics.periods import PeriodSpec
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.shared.errors import ValidationError

MIN_CHANNELS = 2
MAX_CHANNELS = 5


class CompareChannels:
    def __init__(self, get_metrics: GetChannelMetrics) -> None:
        self._get_metrics = get_metrics

    async def execute(
        self, actor: User, channel_ids: list[str], spec: PeriodSpec
    ) -> list[ChannelMetricsDTO]:
        require(actor, Permission.ANALYTICS_READ)
        unique = list(dict.fromkeys(channel_ids))
        if len(unique) < MIN_CHANNELS:
            raise ValidationError(f"Cần chọn ít nhất {MIN_CHANNELS} kênh để so sánh")
        if len(unique) > MAX_CHANNELS:
            raise ValidationError(f"Chỉ so sánh tối đa {MAX_CHANNELS} kênh")
        return [await self._get_metrics.execute(actor, item, spec) for item in unique]
