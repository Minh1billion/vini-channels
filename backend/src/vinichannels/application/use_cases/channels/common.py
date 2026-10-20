from vinichannels.application.errors import NotFound
from vinichannels.application.ports.unit_of_work import UnitOfWork
from vinichannels.domain.channels.entities import Channel
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.partners.errors import PartnerArchived
from vinichannels.domain.shared.ids import ChannelId, PartnerId
from vinichannels.domain.syncing.schedule import SchedulePreset, SyncSchedule


async def load_channel(uow: UnitOfWork, channel_id: str) -> Channel:
    channel = await uow.channels.get(ChannelId(channel_id))
    if channel is None:
        raise NotFound("Không tìm thấy kênh")
    return channel


async def load_active_partner(uow: UnitOfWork, partner_id: str) -> Partner:
    partner = await uow.partners.get(PartnerId(partner_id))
    if partner is None:
        raise NotFound("Không tìm thấy đối tác")
    if partner.is_archived:
        raise PartnerArchived("Đối tác đã được lưu trữ")
    return partner


def validate_schedule(cron: str | None, timezone: str) -> None:
    SyncSchedule.from_cron(cron or SchedulePreset.DAILY.value, timezone)
