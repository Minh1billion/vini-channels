from dataclasses import dataclass

from vinichannels.domain.channels.value_objects import ChannelStatus
from vinichannels.domain.shared.events import DomainEvent
from vinichannels.domain.shared.ids import ChannelId


@dataclass(frozen=True, slots=True)
class ChannelStatusChanged(DomainEvent):
    channel_id: ChannelId
    previous: ChannelStatus
    current: ChannelStatus
