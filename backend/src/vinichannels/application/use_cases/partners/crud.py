from dataclasses import dataclass

from vinichannels.application.authorization import require
from vinichannels.application.dto import UNSET, Maybe, PartnerDTO, Unset
from vinichannels.application.errors import Conflict, NotFound
from vinichannels.application.ports.clock import Clock
from vinichannels.application.ports.unit_of_work import UnitOfWork, UnitOfWorkFactory
from vinichannels.application.use_cases.audit.recording import change, record
from vinichannels.domain.audit.entities import AuditAction
from vinichannels.domain.identity.entities import Permission, User
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.shared.ids import PartnerId, UserId, new_id


async def _load(uow: UnitOfWork, partner_id: str) -> Partner:
    partner = await uow.partners.get(PartnerId(partner_id))
    if partner is None:
        raise NotFound("Không tìm thấy đối tác")
    return partner


async def _ensure_owner(uow: UnitOfWork, owner_user_id: str | None) -> None:
    if owner_user_id is not None and await uow.users.get(UserId(owner_user_id)) is None:
        raise NotFound("Không tìm thấy người phụ trách")


def _apply_tags(partner: Partner, tags: frozenset[str]) -> None:
    partner.tags = frozenset()
    for tag in tags:
        partner.add_tag(tag)


class CreatePartner:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(
        self,
        actor: User,
        name: str,
        industry: str | None = None,
        owner_user_id: str | None = None,
        logo_url: str | None = None,
        notes: str = "",
        tags: frozenset[str] = frozenset(),
    ) -> PartnerDTO:
        require(actor, Permission.PARTNERS_WRITE)
        async with self._uow_factory() as uow:
            partner = Partner(
                id=PartnerId(new_id()),
                name=name,
                industry=industry,
                owner_user_id=UserId(owner_user_id) if owner_user_id else None,
                logo_url=logo_url,
                notes=notes,
            )
            _apply_tags(partner, tags)
            if await uow.partners.get_by_name(partner.name) is not None:
                raise Conflict("Tên đối tác đã tồn tại")
            await _ensure_owner(uow, owner_user_id)
            await uow.partners.add(partner)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.PARTNER_CREATE,
                "partner",
                partner.id,
                partner.name,
            )
            await uow.commit()
        return PartnerDTO.from_entity(partner)


@dataclass(frozen=True, slots=True)
class UpdatePartnerCommand:
    partner_id: str
    name: Maybe[str] = UNSET
    industry: Maybe[str | None] = UNSET
    owner_user_id: Maybe[str | None] = UNSET
    logo_url: Maybe[str | None] = UNSET
    notes: Maybe[str] = UNSET
    tags: Maybe[frozenset[str]] = UNSET


class UpdatePartner:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, command: UpdatePartnerCommand) -> PartnerDTO:
        require(actor, Permission.PARTNERS_WRITE)
        async with self._uow_factory() as uow:
            partner = await _load(uow, command.partner_id)
            changes: dict[str, str] = {}
            if not isinstance(command.name, Unset):
                previous_name = partner.name
                partner.rename(command.name)
                if partner.name != previous_name:
                    changes["name"] = change(previous_name, partner.name)
                other = await uow.partners.get_by_name(partner.name)
                if other is not None and other.id != partner.id:
                    raise Conflict("Tên đối tác đã tồn tại")
            if not isinstance(command.industry, Unset):
                if command.industry != partner.industry:
                    changes["industry"] = change(partner.industry, command.industry)
                partner.industry = command.industry
            if not isinstance(command.owner_user_id, Unset):
                await _ensure_owner(uow, command.owner_user_id)
                owner = command.owner_user_id
                if (owner or None) != partner.owner_user_id:
                    changes["owner"] = change(partner.owner_user_id, owner)
                partner.owner_user_id = UserId(owner) if owner else None
            if not isinstance(command.logo_url, Unset):
                if command.logo_url != partner.logo_url:
                    changes["logo_url"] = "changed"
                partner.logo_url = command.logo_url
            if not isinstance(command.notes, Unset):
                if command.notes != partner.notes:
                    changes["notes"] = "changed"
                partner.notes = command.notes
            if not isinstance(command.tags, Unset):
                before_tags = partner.tags
                _apply_tags(partner, command.tags)
                if partner.tags != before_tags:
                    changes["tags"] = change(
                        ", ".join(sorted(before_tags)), ", ".join(sorted(partner.tags))
                    )
            await uow.partners.save(partner)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.PARTNER_UPDATE,
                "partner",
                partner.id,
                partner.name,
                changes,
            )
            await uow.commit()
            counts = await uow.channels.active_counts_by_partner()
        return PartnerDTO.from_entity(partner, counts.get(partner.id, 0))


class ArchivePartner:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, partner_id: str) -> PartnerDTO:
        require(actor, Permission.PARTNERS_WRITE)
        now = self._clock.now()
        async with self._uow_factory() as uow:
            partner = await _load(uow, partner_id)
            partner.archive(now)
            await uow.partners.save(partner)
            for channel in await uow.channels.list_all(partner_id=partner.id):
                channel.archive(now)
                await uow.channels.save(channel)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.PARTNER_ARCHIVE,
                "partner",
                partner.id,
                partner.name,
            )
            await uow.commit()
        return PartnerDTO.from_entity(partner)


class RestorePartner:
    def __init__(self, uow_factory: UnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    async def execute(self, actor: User, partner_id: str) -> PartnerDTO:
        require(actor, Permission.PARTNERS_WRITE)
        async with self._uow_factory() as uow:
            partner = await _load(uow, partner_id)
            partner.restore()
            await uow.partners.save(partner)
            await record(
                uow,
                self._clock,
                actor,
                AuditAction.PARTNER_RESTORE,
                "partner",
                partner.id,
                partner.name,
            )
            await uow.commit()
            counts = await uow.channels.active_counts_by_partner()
        return PartnerDTO.from_entity(partner, counts.get(partner.id, 0))


class GetPartner:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, actor: User, partner_id: str) -> PartnerDTO:
        require(actor, Permission.PARTNERS_READ)
        async with self._uow_factory() as uow:
            partner = await _load(uow, partner_id)
            counts = await uow.channels.active_counts_by_partner()
        return PartnerDTO.from_entity(partner, counts.get(partner.id, 0))


class ListPartners:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(
        self,
        actor: User,
        include_archived: bool = False,
        tag: str | None = None,
        search: str | None = None,
    ) -> list[PartnerDTO]:
        require(actor, Permission.PARTNERS_READ)
        async with self._uow_factory() as uow:
            partners = await uow.partners.list_all(include_archived, tag, search)
            counts = await uow.channels.active_counts_by_partner()
        return [PartnerDTO.from_entity(p, counts.get(p.id, 0)) for p in partners]
