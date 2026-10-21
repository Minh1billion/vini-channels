from dataclasses import dataclass
from typing import Protocol

from vinichannels.domain.notifications.entities import PushSubscription


@dataclass(frozen=True, slots=True)
class PushMessage:
    title: str
    body: str
    url: str
    tag: str


class PushSubscriptionGone(Exception):
    pass


class PushSender(Protocol):
    async def send(self, subscription: PushSubscription, message: PushMessage) -> None: ...
