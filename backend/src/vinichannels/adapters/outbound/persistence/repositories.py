from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute
from sqlalchemy.sql import ColumnElement

from vinichannels.adapters.outbound.persistence.mappers import (
    SCORING_ROW_ID,
    apply_channel,
    apply_credential,
    apply_partner,
    apply_provider,
    apply_scoring,
    apply_sync_run,
    apply_user,
    apply_video,
    audit_to_domain,
    audit_to_model,
    channel_snapshot_to_domain,
    channel_snapshot_to_model,
    channel_to_domain,
    credential_to_domain,
    notification_to_domain,
    notification_to_model,
    partner_to_domain,
    provider_to_domain,
    push_subscription_to_domain,
    push_subscription_to_model,
    scoring_to_domain,
    sync_run_to_domain,
    user_to_domain,
    video_snapshot_to_domain,
    video_snapshot_to_model,
    video_to_domain,
)
from vinichannels.adapters.outbound.persistence.models import (
    AuditLogModel,
    ChannelCredentialModel,
    ChannelModel,
    ChannelSnapshotModel,
    NotificationModel,
    PartnerModel,
    PartnerTagModel,
    ProviderConfigModel,
    PushSubscriptionModel,
    ScoringSettingsModel,
    SyncRunModel,
    UserModel,
    VideoModel,
    VideoSnapshotModel,
)
from vinichannels.application.errors import Conflict, DuplicateSyncRun
from vinichannels.application.ports.repositories import AuditFilter
from vinichannels.domain.analytics.scoring import ScoreWeights
from vinichannels.domain.audit.entities import AuditEntry
from vinichannels.domain.channels.entities import Channel, ChannelCredential
from vinichannels.domain.channels.value_objects import Handle
from vinichannels.domain.content.entities import Video
from vinichannels.domain.content.snapshots import ChannelSnapshot, VideoSnapshot
from vinichannels.domain.identity.entities import User
from vinichannels.domain.notifications.entities import Notification, PushSubscription
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.shared.ids import ChannelId, PartnerId, SyncRunId, UserId, VideoId
from vinichannels.domain.syncing.entities import SyncRun, SyncStatus
from vinichannels.domain.syncing.providers import ProviderConfig, ProviderKey


async def _flush(
    session: AsyncSession, message: str, error_type: type[Conflict] = Conflict
) -> None:
    try:
        await session.flush()
    except IntegrityError as error:
        raise error_type(message) from error


def _contains(column: QueryableAttribute[Any], search: str) -> ColumnElement[bool]:
    escaped = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


class SqlUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        model = UserModel()
        apply_user(model, user)
        self._session.add(model)
        await _flush(self._session, "Email đã được sử dụng")

    async def save(self, user: User) -> None:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            await self.add(user)
            return
        apply_user(model, user)
        await _flush(self._session, "Email đã được sử dụng")

    async def get(self, user_id: UserId) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return user_to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.scalars(
            select(UserModel).where(UserModel.email == email.strip().lower())
        )
        model = result.first()
        return user_to_domain(model) if model else None

    async def list_all(self) -> list[User]:
        result = await self._session.scalars(select(UserModel).order_by(UserModel.email))
        return [user_to_domain(model) for model in result.all()]

    async def count(self) -> int:
        result = await self._session.scalar(select(func.count()).select_from(UserModel))
        return result or 0


class SqlPartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, partner: Partner) -> None:
        model = PartnerModel()
        apply_partner(model, partner)
        self._session.add(model)
        await _flush(self._session, "Tên đối tác đã tồn tại")

    async def save(self, partner: Partner) -> None:
        model = await self._session.get(PartnerModel, partner.id)
        if model is None:
            await self.add(partner)
            return
        apply_partner(model, partner)
        await _flush(self._session, "Tên đối tác đã tồn tại")

    async def get(self, partner_id: PartnerId) -> Partner | None:
        model = await self._session.get(PartnerModel, partner_id)
        return partner_to_domain(model) if model else None

    async def get_by_name(self, name: str) -> Partner | None:
        result = await self._session.scalars(
            select(PartnerModel).where(func.lower(PartnerModel.name) == name.strip().lower())
        )
        model = result.first()
        return partner_to_domain(model) if model else None

    async def list_all(
        self,
        include_archived: bool = False,
        tag: str | None = None,
        search: str | None = None,
    ) -> list[Partner]:
        statement = select(PartnerModel).order_by(func.lower(PartnerModel.name))
        if not include_archived:
            statement = statement.where(PartnerModel.archived_at.is_(None))
        if tag:
            statement = statement.where(
                PartnerModel.tags.any(PartnerTagModel.tag == tag.strip().lower())
            )
        if search and search.strip():
            statement = statement.where(
                or_(_contains(PartnerModel.name, search), _contains(PartnerModel.industry, search))
            )
        result = await self._session.scalars(statement)
        return [partner_to_domain(model) for model in result.all()]


class SqlChannelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, channel: Channel) -> None:
        model = ChannelModel()
        apply_channel(model, channel)
        self._session.add(model)
        await _flush(self._session, f"Kênh {channel.handle.display} đã tồn tại")

    async def save(self, channel: Channel) -> None:
        model = await self._session.get(ChannelModel, channel.id)
        if model is None:
            await self.add(channel)
            return
        apply_channel(model, channel)
        await _flush(self._session, f"Kênh {channel.handle.display} đã tồn tại")

    async def get(self, channel_id: ChannelId) -> Channel | None:
        model = await self._session.get(ChannelModel, channel_id)
        return channel_to_domain(model) if model else None

    async def get_by_handle(self, handle: Handle) -> Channel | None:
        result = await self._session.scalars(
            select(ChannelModel).where(ChannelModel.handle == handle.value)
        )
        model = result.first()
        return channel_to_domain(model) if model else None

    async def list_all(
        self,
        partner_id: PartnerId | None = None,
        include_archived: bool = False,
        search: str | None = None,
    ) -> list[Channel]:
        statement = select(ChannelModel).order_by(ChannelModel.handle)
        if partner_id is not None:
            statement = statement.where(ChannelModel.partner_id == partner_id)
        if not include_archived:
            statement = statement.where(ChannelModel.archived_at.is_(None))
        if search and search.strip():
            statement = statement.where(
                or_(
                    _contains(ChannelModel.handle, search),
                    _contains(ChannelModel.display_name, search),
                )
            )
        result = await self._session.scalars(statement)
        return [channel_to_domain(model) for model in result.all()]

    async def active_counts_by_partner(self) -> dict[PartnerId, int]:
        result = await self._session.execute(
            select(ChannelModel.partner_id, func.count())
            .where(ChannelModel.archived_at.is_(None))
            .group_by(ChannelModel.partner_id)
        )
        return {PartnerId(partner_id): count for partner_id, count in result.all()}


class SqlChannelCredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, channel_id: ChannelId) -> ChannelCredential | None:
        model = await self._session.get(ChannelCredentialModel, channel_id)
        return credential_to_domain(model) if model else None

    async def save(self, credential: ChannelCredential) -> None:
        model = await self._session.get(ChannelCredentialModel, credential.channel_id)
        if model is None:
            model = ChannelCredentialModel()
            self._session.add(model)
        apply_credential(model, credential)
        await self._session.flush()


class SqlProviderConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: ProviderKey) -> ProviderConfig | None:
        model = await self._session.get(ProviderConfigModel, key.value)
        return provider_to_domain(model) if model else None

    async def save(self, config: ProviderConfig) -> None:
        model = await self._session.get(ProviderConfigModel, config.key.value)
        if model is None:
            model = ProviderConfigModel()
            self._session.add(model)
        apply_provider(model, config)
        await self._session.flush()

    async def list_all(self) -> list[ProviderConfig]:
        result = await self._session.scalars(select(ProviderConfigModel))
        known = {key.value for key in ProviderKey}
        return [provider_to_domain(model) for model in result.all() if model.key in known]


class SqlSyncRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, run: SyncRun) -> None:
        model = SyncRunModel()
        apply_sync_run(model, run)
        self._session.add(model)
        await _flush(self._session, "Lần đồng bộ này đã được tạo", DuplicateSyncRun)

    async def save(self, run: SyncRun) -> None:
        model = await self._session.get(SyncRunModel, run.id)
        if model is None:
            await self.add(run)
            return
        apply_sync_run(model, run)
        await self._session.flush()

    async def get(self, run_id: SyncRunId) -> SyncRun | None:
        model = await self._session.get(SyncRunModel, run_id)
        return sync_run_to_domain(model) if model else None

    async def count_usage(self, source: str, since: datetime) -> int:
        result = await self._session.scalar(
            select(func.count())
            .select_from(SyncRunModel)
            .where(
                SyncRunModel.source == source,
                SyncRunModel.started_at >= since,
                SyncRunModel.status.in_([SyncStatus.SUCCESS.value, SyncStatus.PARTIAL.value]),
            )
        )
        return result or 0

    async def latest_slots(self) -> dict[ChannelId, datetime]:
        result = await self._session.execute(
            select(SyncRunModel.channel_id, func.max(SyncRunModel.scheduled_for)).group_by(
                SyncRunModel.channel_id
            )
        )
        return {ChannelId(channel_id): slot for channel_id, slot in result.all()}

    async def list_recent(
        self,
        limit: int,
        status: SyncStatus | None = None,
        channel_id: ChannelId | None = None,
    ) -> list[SyncRun]:
        query = select(SyncRunModel).order_by(SyncRunModel.started_at.desc()).limit(limit)
        if status is not None:
            query = query.where(SyncRunModel.status == status.value)
        if channel_id is not None:
            query = query.where(SyncRunModel.channel_id == channel_id)
        result = await self._session.scalars(query)
        return [sync_run_to_domain(model) for model in result.all()]


class SqlVideoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_platform_ids(
        self, channel_id: ChannelId, platform_video_ids: Sequence[str]
    ) -> dict[str, Video]:
        if not platform_video_ids:
            return {}
        result = await self._session.scalars(
            select(VideoModel).where(
                VideoModel.channel_id == channel_id,
                VideoModel.platform_video_id.in_(platform_video_ids),
            )
        )
        return {model.platform_video_id: video_to_domain(model) for model in result.all()}

    async def save(self, video: Video) -> None:
        model = await self._session.get(VideoModel, video.id)
        if model is None:
            model = VideoModel()
            self._session.add(model)
        apply_video(model, video)
        await self._session.flush()

    async def list_for_channel(
        self,
        channel_id: ChannelId,
        posted_from: datetime | None = None,
        posted_until: datetime | None = None,
    ) -> list[Video]:
        query = select(VideoModel).where(VideoModel.channel_id == channel_id)
        if posted_from is not None:
            query = query.where(VideoModel.posted_at >= posted_from)
        if posted_until is not None:
            query = query.where(VideoModel.posted_at < posted_until)
        result = await self._session.scalars(query.order_by(VideoModel.posted_at.desc()))
        return [video_to_domain(model) for model in result.all()]

    async def search(self, text: str, limit: int) -> list[Video]:
        result = await self._session.scalars(
            select(VideoModel)
            .where(_contains(VideoModel.caption, text))
            .order_by(VideoModel.posted_at.desc())
            .limit(limit)
        )
        return [video_to_domain(model) for model in result.all()]


class SqlSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_channel_snapshot(self, snapshot: ChannelSnapshot) -> None:
        self._session.add(channel_snapshot_to_model(snapshot))
        await self._session.flush()

    async def add_video_snapshots(self, snapshots: Sequence[VideoSnapshot]) -> None:
        self._session.add_all([video_snapshot_to_model(item) for item in snapshots])
        await self._session.flush()

    async def latest_channel_snapshot(self, channel_id: ChannelId) -> ChannelSnapshot | None:
        result = await self._session.scalars(
            select(ChannelSnapshotModel)
            .where(ChannelSnapshotModel.channel_id == channel_id)
            .order_by(ChannelSnapshotModel.captured_at.desc())
            .limit(1)
        )
        model = result.first()
        return channel_snapshot_to_domain(model) if model else None

    async def channel_snapshots(
        self, channel_id: ChannelId, since: datetime, until: datetime
    ) -> list[ChannelSnapshot]:
        result = await self._session.scalars(
            select(ChannelSnapshotModel)
            .where(
                ChannelSnapshotModel.channel_id == channel_id,
                ChannelSnapshotModel.captured_at >= since,
                ChannelSnapshotModel.captured_at < until,
            )
            .order_by(ChannelSnapshotModel.captured_at)
        )
        return [channel_snapshot_to_domain(model) for model in result.all()]

    async def video_snapshots(
        self, video_ids: Sequence[VideoId], since: datetime, until: datetime
    ) -> list[VideoSnapshot]:
        if not video_ids:
            return []
        result = await self._session.scalars(
            select(VideoSnapshotModel)
            .where(
                VideoSnapshotModel.video_id.in_(video_ids),
                VideoSnapshotModel.captured_at >= since,
                VideoSnapshotModel.captured_at < until,
            )
            .order_by(VideoSnapshotModel.captured_at)
        )
        return [video_snapshot_to_domain(model) for model in result.all()]

    async def earliest_activity(
        self, channel_ids: Sequence[ChannelId] | None = None
    ) -> datetime | None:
        snapshot_query = select(func.min(ChannelSnapshotModel.captured_at))
        video_query = select(func.min(VideoModel.posted_at))
        if channel_ids is not None:
            snapshot_query = snapshot_query.where(ChannelSnapshotModel.channel_id.in_(channel_ids))
            video_query = video_query.where(VideoModel.channel_id.in_(channel_ids))
        found = (
            await self._session.scalar(snapshot_query),
            await self._session.scalar(video_query),
        )
        return min((stamp for stamp in found if stamp is not None), default=None)


class SqlScoringSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> ScoreWeights | None:
        model = await self._session.get(ScoringSettingsModel, SCORING_ROW_ID)
        return scoring_to_domain(model) if model else None

    async def save(self, weights: ScoreWeights) -> None:
        model = await self._session.get(ScoringSettingsModel, SCORING_ROW_ID)
        if model is None:
            model = ScoringSettingsModel()
            self._session.add(model)
        apply_scoring(model, weights)
        await self._session.flush()


class SqlAuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entry: AuditEntry) -> None:
        self._session.add(audit_to_model(entry))
        await self._session.flush()

    async def search(self, criteria: AuditFilter, limit: int, offset: int) -> list[AuditEntry]:
        query = select(AuditLogModel)
        if criteria.actor_id:
            query = query.where(AuditLogModel.actor_id == criteria.actor_id)
        if criteria.action:
            query = query.where(AuditLogModel.action == criteria.action.value)
        if criteria.since:
            query = query.where(AuditLogModel.occurred_at >= criteria.since)
        if criteria.until:
            query = query.where(AuditLogModel.occurred_at < criteria.until)
        query = query.order_by(AuditLogModel.occurred_at.desc(), AuditLogModel.id).limit(limit)
        rows = await self._session.scalars(query.offset(offset))
        return [audit_to_domain(row) for row in rows]


class SqlNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, notification: Notification) -> None:
        self._session.add(notification_to_model(notification))
        await self._session.flush()

    async def exists(self, dedupe_key: str) -> bool:
        found = await self._session.scalar(
            select(NotificationModel.id).where(NotificationModel.dedupe_key == dedupe_key)
        )
        return found is not None

    async def get(self, notification_id: str) -> Notification | None:
        model = await self._session.get(NotificationModel, notification_id)
        return notification_to_domain(model) if model else None

    async def save(self, notification: Notification) -> None:
        model = await self._session.get(NotificationModel, notification.id)
        if model is not None:
            model.read_at = notification.read_at
            await self._session.flush()

    async def list_recent(self, limit: int, unread_only: bool = False) -> list[Notification]:
        query = select(NotificationModel)
        if unread_only:
            query = query.where(NotificationModel.read_at.is_(None))
        rows = await self._session.scalars(
            query.order_by(NotificationModel.created_at.desc(), NotificationModel.id).limit(limit)
        )
        return [notification_to_domain(row) for row in rows]

    async def count_unread(self) -> int:
        total = await self._session.scalar(
            select(func.count())
            .select_from(NotificationModel)
            .where(NotificationModel.read_at.is_(None))
        )
        return int(total or 0)

    async def mark_all_read(self, at: datetime) -> int:
        result = await self._session.execute(
            update(NotificationModel).where(NotificationModel.read_at.is_(None)).values(read_at=at)
        )
        await self._session.flush()
        return int(getattr(result, "rowcount", 0) or 0)


class SqlPushSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, subscription: PushSubscription) -> None:
        model = await self._session.scalar(
            select(PushSubscriptionModel).where(
                PushSubscriptionModel.endpoint == subscription.endpoint
            )
        )
        if model is None:
            self._session.add(push_subscription_to_model(subscription))
        else:
            model.user_id = subscription.user_id
            model.p256dh = subscription.p256dh
            model.auth = subscription.auth
        await self._session.flush()

    async def remove(self, user_id: UserId, endpoint: str) -> None:
        await self._session.execute(
            delete(PushSubscriptionModel).where(
                PushSubscriptionModel.user_id == user_id,
                PushSubscriptionModel.endpoint == endpoint,
            )
        )
        await self._session.flush()

    async def remove_endpoints(self, endpoints: Sequence[str]) -> None:
        if not endpoints:
            return
        await self._session.execute(
            delete(PushSubscriptionModel).where(PushSubscriptionModel.endpoint.in_(endpoints))
        )
        await self._session.flush()

    async def list_all(self) -> list[PushSubscription]:
        rows = await self._session.scalars(
            select(PushSubscriptionModel).order_by(PushSubscriptionModel.created_at)
        )
        return [push_subscription_to_domain(row) for row in rows]
