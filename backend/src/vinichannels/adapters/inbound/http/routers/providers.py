from fastapi import APIRouter

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.common import given, given_nullable
from vinichannels.adapters.inbound.http.schemas.sync import (
    ProviderResponse,
    ProviderUpdateRequest,
)
from vinichannels.application.use_cases.syncing.providers import UpdateProviderCommand

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers(user: CurrentUser, use_cases: UseCasesDep) -> list[ProviderResponse]:
    items = await use_cases.list_providers.execute(user)
    return [ProviderResponse.model_validate(item) for item in items]


@router.put("/{key}")
async def update_provider(
    key: str, body: ProviderUpdateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> ProviderResponse:
    command = UpdateProviderCommand(
        key=key,
        enabled=given(body.enabled),
        priority=given(body.priority),
        monthly_quota=given_nullable(body, "monthly_quota", body.monthly_quota),
        credentials=given(body.credentials),
    )
    return ProviderResponse.model_validate(await use_cases.update_provider.execute(user, command))
