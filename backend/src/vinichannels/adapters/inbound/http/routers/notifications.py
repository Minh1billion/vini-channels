from typing import Annotated

from fastapi import APIRouter, Query, status

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.notifications import (
    NotificationListResponse,
    NotificationResponse,
    PushConfigResponse,
    PushSubscribeRequest,
    PushUnsubscribeRequest,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    user: CurrentUser,
    use_cases: UseCasesDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    unread_only: bool = False,
) -> NotificationListResponse:
    result = await use_cases.list_notifications.execute(user, limit, unread_only)
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in result.items],
        unread_count=result.unread_count,
    )


@router.get("/push/config")
async def push_config(user: CurrentUser, use_cases: UseCasesDep) -> PushConfigResponse:
    public_key = use_cases.get_push_config.execute(user)
    return PushConfigResponse(enabled=public_key is not None, public_key=public_key)


@router.post("/push/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def push_subscribe(
    body: PushSubscribeRequest, user: CurrentUser, use_cases: UseCasesDep
) -> None:
    await use_cases.subscribe_push.execute(user, body.endpoint, body.p256dh, body.auth)


@router.post("/push/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def push_unsubscribe(
    body: PushUnsubscribeRequest, user: CurrentUser, use_cases: UseCasesDep
) -> None:
    await use_cases.unsubscribe_push.execute(user, body.endpoint)


@router.post("/read-all")
async def read_all(user: CurrentUser, use_cases: UseCasesDep) -> dict[str, int]:
    return {"updated": await use_cases.mark_all_notifications_read.execute(user)}


@router.post("/{notification_id}/read")
async def read_one(
    notification_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> NotificationResponse:
    item = await use_cases.mark_notification_read.execute(user, notification_id)
    return NotificationResponse.model_validate(item)
