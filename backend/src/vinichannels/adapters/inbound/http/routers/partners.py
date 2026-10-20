from typing import Annotated

from fastapi import APIRouter, Query, status

from vinichannels.adapters.inbound.http.dependencies import CurrentUser, UseCasesDep
from vinichannels.adapters.inbound.http.schemas.common import given, given_nullable
from vinichannels.adapters.inbound.http.schemas.partners import (
    PartnerCreateRequest,
    PartnerResponse,
    PartnerUpdateRequest,
)
from vinichannels.application.dto import UNSET
from vinichannels.application.use_cases.partners.crud import UpdatePartnerCommand

router = APIRouter(prefix="/partners", tags=["partners"])


@router.get("")
async def list_partners(
    user: CurrentUser,
    use_cases: UseCasesDep,
    include_archived: bool = False,
    tag: str | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[PartnerResponse]:
    items = await use_cases.list_partners.execute(user, include_archived, tag, q)
    return [PartnerResponse.model_validate(item) for item in items]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_partner(
    body: PartnerCreateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> PartnerResponse:
    created = await use_cases.create_partner.execute(
        user,
        name=body.name,
        industry=body.industry,
        owner_user_id=body.owner_user_id,
        logo_url=body.logo_url,
        notes=body.notes,
        tags=frozenset(body.tags),
    )
    return PartnerResponse.model_validate(created)


@router.get("/{partner_id}")
async def get_partner(
    partner_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> PartnerResponse:
    return PartnerResponse.model_validate(await use_cases.get_partner.execute(user, partner_id))


@router.patch("/{partner_id}")
async def update_partner(
    partner_id: str, body: PartnerUpdateRequest, user: CurrentUser, use_cases: UseCasesDep
) -> PartnerResponse:
    command = UpdatePartnerCommand(
        partner_id=partner_id,
        name=given(body.name),
        industry=given_nullable(body, "industry", body.industry),
        owner_user_id=given_nullable(body, "owner_user_id", body.owner_user_id),
        logo_url=given_nullable(body, "logo_url", body.logo_url),
        notes=given(body.notes),
        tags=UNSET if body.tags is None else frozenset(body.tags),
    )
    return PartnerResponse.model_validate(await use_cases.update_partner.execute(user, command))


@router.delete("/{partner_id}")
async def archive_partner(
    partner_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> PartnerResponse:
    return PartnerResponse.model_validate(await use_cases.archive_partner.execute(user, partner_id))


@router.post("/{partner_id}/restore")
async def restore_partner(
    partner_id: str, user: CurrentUser, use_cases: UseCasesDep
) -> PartnerResponse:
    return PartnerResponse.model_validate(await use_cases.restore_partner.execute(user, partner_id))
