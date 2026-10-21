import asyncio
import json

from py_vapid import Vapid
from pywebpush import WebPushException, webpush

from vinichannels.application.ports.push import PushMessage, PushSubscriptionGone
from vinichannels.domain.notifications.entities import PushSubscription

GONE_STATUSES = frozenset({404, 410})


class WebPushSender:
    def __init__(self, private_key: str, subject: str, ttl_sec: int = 86400) -> None:
        self._vapid = Vapid.from_string(private_key)
        self._subject = subject
        self._ttl = ttl_sec

    async def send(self, subscription: PushSubscription, message: PushMessage) -> None:
        await asyncio.to_thread(self._send, subscription, message)

    def _send(self, subscription: PushSubscription, message: PushMessage) -> None:
        payload = json.dumps(
            {
                "title": message.title,
                "body": message.body,
                "url": message.url,
                "tag": message.tag,
            }
        )
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=self._vapid,
                vapid_claims={"sub": self._subject},
                ttl=self._ttl,
            )
        except WebPushException as error:
            status = getattr(error.response, "status_code", None)
            if status in GONE_STATUSES:
                raise PushSubscriptionGone(subscription.endpoint) from error
            raise
