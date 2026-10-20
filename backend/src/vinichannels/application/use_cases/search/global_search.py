from vinichannels.application.dto import ChannelDTO, PartnerDTO, SearchResultDTO, SearchVideoHit
from vinichannels.application.ports.unit_of_work import UnitOfWorkFactory
from vinichannels.domain.identity.entities import Permission, User

MIN_QUERY_LENGTH = 2
MAX_LIMIT = 10


class GlobalSearch:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, actor: User, text: str, limit: int = 5) -> SearchResultDTO:
        needle = text.strip()
        capped = max(1, min(limit, MAX_LIMIT))
        if len(needle) < MIN_QUERY_LENGTH:
            return SearchResultDTO([], [], [])
        partners: list[PartnerDTO] = []
        channels: list[ChannelDTO] = []
        videos: list[SearchVideoHit] = []
        async with self._uow_factory() as uow:
            if actor.can(Permission.PARTNERS_READ):
                found_partners = await uow.partners.list_all(search=needle)
                counts = await uow.channels.active_counts_by_partner()
                partners = [
                    PartnerDTO.from_entity(partner, counts.get(partner.id, 0))
                    for partner in found_partners[:capped]
                ]
                found_channels = await uow.channels.list_all(search=needle)
                channels = [ChannelDTO.from_entity(channel) for channel in found_channels[:capped]]
            if actor.can(Permission.ANALYTICS_READ):
                for video in await uow.videos.search(needle, capped * 3):
                    channel = await uow.channels.get(video.channel_id)
                    if channel is None or channel.is_archived:
                        continue
                    videos.append(
                        SearchVideoHit(
                            id=video.id,
                            channel_id=video.channel_id,
                            handle=channel.handle.value,
                            caption=video.caption,
                            thumbnail_url=video.thumbnail_url,
                            posted_at=video.posted_at,
                        )
                    )
                    if len(videos) == capped:
                        break
        return SearchResultDTO(partners, channels, videos)
