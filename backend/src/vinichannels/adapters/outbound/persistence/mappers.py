import json

from vinichannels.adapters.outbound.persistence.models import (
    AuditLogModel,
    NotificationModel,
    PushSubscriptionModel,
    ChannelCredentialModel,
    ChannelModel,
    ChannelSnapshotModel,
    PartnerModel,
    PartnerTagModel,
    ProviderConfigModel,
    ScoringSettingsModel,
    SyncRunModel,
    UserModel,
    VideoModel,
    VideoSnapshotModel,
)
from vinichannels.domain.analytics.scoring import ScoreWeights
from vinichannels.domain.audit.entities import AuditAction, AuditEntry
from vinichannels.domain.channels.entities import Channel, ChannelCredential
from vinichannels.domain.channels.value_objects import ChannelStatus, ConnectionMode, Handle
from vinichannels.domain.content.entities import Video
from vinichannels.domain.content.snapshots import ChannelSnapshot, VideoSnapshot
from vinichannels.domain.identity.entities import Role, User
from vinichannels.domain.notifications.entities import (
    Notification,
    NotificationKind,
    PushSubscription,
)
from vinichannels.domain.partners.entities import Partner
from vinichannels.domain.shared.ids import ChannelId, PartnerId, SyncRunId, UserId, VideoId
from vinichannels.domain.syncing.entities import SyncRun, SyncStatus, SyncTrigger
from vinichannels.domain.syncing.providers import ProviderConfig, ProviderKey

SCORING_ROW_ID = 1


def user_to_domain(model: UserModel) -> User:
    return User(
        id=UserId(model.id),
        email=model.email,
        role=Role(model.role),
        password_hash=model.password_hash,
        is_active=model.is_active,
        failed_login_attempts=model.failed_login_attempts,
        locked_until=model.locked_until,
    )


def apply_user(model: UserModel, user: User) -> None:
    model.id = user.id
    model.email = user.email
    model.role = user.role.value
    model.password_hash = user.password_hash
    model.is_active = user.is_active
    model.failed_login_attempts = user.failed_login_attempts
    model.locked_until = user.locked_until


def partner_to_domain(model: PartnerModel) -> Partner:
    return Partner(
        id=PartnerId(model.id),
        name=model.name,
        industry=model.industry,
        owner_user_id=UserId(model.owner_user_id) if model.owner_user_id else None,
        logo_url=model.logo_url,
        notes=model.notes,
        tags=frozenset(tag.tag for tag in model.tags),
        archived_at=model.archived_at,
    )


def apply_partner(model: PartnerModel, partner: Partner) -> None:
    model.id = partner.id
    model.name = partner.name
    model.industry = partner.industry
    model.owner_user_id = partner.owner_user_id
    model.logo_url = partner.logo_url
    model.notes = partner.notes
    model.archived_at = partner.archived_at
    existing = {tag.tag: tag for tag in model.tags}
    for name, tag in existing.items():
        if name not in partner.tags:
            model.tags.remove(tag)
    for name in partner.tags:
        if name not in existing:
            model.tags.append(PartnerTagModel(tag=name))


def channel_to_domain(model: ChannelModel) -> Channel:
    return Channel(
        id=ChannelId(model.id),
        partner_id=PartnerId(model.partner_id),
        handle=Handle(model.handle),
        display_name=model.display_name,
        connection_mode=ConnectionMode(model.connection_mode),
        status=ChannelStatus(model.status),
        platform_channel_id=model.platform_channel_id,
        avatar_url=model.avatar_url,
        sync_cron=model.sync_cron,
        timezone=model.timezone,
        is_active=model.is_active,
        archived_at=model.archived_at,
    )


def apply_channel(model: ChannelModel, channel: Channel) -> None:
    model.id = channel.id
    model.partner_id = channel.partner_id
    model.platform_channel_id = channel.platform_channel_id
    model.handle = channel.handle.value
    model.display_name = channel.display_name
    model.avatar_url = channel.avatar_url
    model.connection_mode = channel.connection_mode.value
    model.status = channel.status.value
    model.sync_cron = channel.sync_cron
    model.timezone = channel.timezone
    model.is_active = channel.is_active
    model.archived_at = channel.archived_at


def credential_to_domain(model: ChannelCredentialModel) -> ChannelCredential:
    return ChannelCredential(
        channel_id=ChannelId(model.channel_id),
        access_token_enc=model.access_token_enc,
        refresh_token_enc=model.refresh_token_enc,
        expires_at=model.expires_at,
        refresh_expires_at=model.refresh_expires_at,
        scopes=frozenset(model.scopes.split()),
    )


def apply_credential(model: ChannelCredentialModel, credential: ChannelCredential) -> None:
    model.channel_id = credential.channel_id
    model.access_token_enc = credential.access_token_enc
    model.refresh_token_enc = credential.refresh_token_enc
    model.expires_at = credential.expires_at
    model.refresh_expires_at = credential.refresh_expires_at
    model.scopes = " ".join(sorted(credential.scopes))


def provider_to_domain(model: ProviderConfigModel) -> ProviderConfig:
    return ProviderConfig(
        key=ProviderKey(model.key),
        enabled=model.enabled,
        priority=model.priority,
        monthly_quota=model.monthly_quota,
        credentials_enc=model.credentials_enc,
    )


def apply_provider(model: ProviderConfigModel, config: ProviderConfig) -> None:
    model.key = config.key.value
    model.enabled = config.enabled
    model.priority = config.priority
    model.monthly_quota = config.monthly_quota
    model.credentials_enc = config.credentials_enc


def sync_run_to_domain(model: SyncRunModel) -> SyncRun:
    return SyncRun(
        id=SyncRunId(model.id),
        channel_id=ChannelId(model.channel_id),
        scheduled_for=model.scheduled_for,
        trigger=SyncTrigger(model.trigger),
        started_at=model.started_at,
        status=SyncStatus(model.status),
        finished_at=model.finished_at,
        source=model.source,
        items_fetched=model.items_fetched,
        error_code=model.error_code,
        error_message=model.error_message,
    )


def apply_sync_run(model: SyncRunModel, run: SyncRun) -> None:
    model.id = run.id
    model.channel_id = run.channel_id
    model.scheduled_for = run.scheduled_for
    model.trigger = run.trigger.value
    model.started_at = run.started_at
    model.status = run.status.value
    model.finished_at = run.finished_at
    model.source = run.source
    model.items_fetched = run.items_fetched
    model.error_code = run.error_code
    model.error_message = run.error_message


def video_to_domain(model: VideoModel) -> Video:
    return Video(
        id=VideoId(model.id),
        channel_id=ChannelId(model.channel_id),
        platform_video_id=model.platform_video_id,
        posted_at=model.posted_at,
        url=model.url,
        caption=model.caption,
        thumbnail_url=model.thumbnail_url,
        duration_sec=model.duration_sec,
    )


def apply_video(model: VideoModel, video: Video) -> None:
    model.id = video.id
    model.channel_id = video.channel_id
    model.platform_video_id = video.platform_video_id
    model.posted_at = video.posted_at
    model.url = video.url
    model.caption = video.caption
    model.thumbnail_url = video.thumbnail_url
    model.duration_sec = video.duration_sec


def channel_snapshot_to_model(snapshot: ChannelSnapshot) -> ChannelSnapshotModel:
    return ChannelSnapshotModel(
        channel_id=snapshot.channel_id,
        captured_at=snapshot.captured_at,
        source=snapshot.source,
        followers=snapshot.followers,
        following=snapshot.following,
        total_likes=snapshot.total_likes,
        video_count=snapshot.video_count,
    )


def channel_snapshot_to_domain(model: ChannelSnapshotModel) -> ChannelSnapshot:
    return ChannelSnapshot(
        channel_id=ChannelId(model.channel_id),
        captured_at=model.captured_at,
        source=model.source,
        followers=model.followers,
        following=model.following,
        total_likes=model.total_likes,
        video_count=model.video_count,
    )


def video_snapshot_to_model(snapshot: VideoSnapshot) -> VideoSnapshotModel:
    return VideoSnapshotModel(
        video_id=snapshot.video_id,
        captured_at=snapshot.captured_at,
        source=snapshot.source,
        views=snapshot.views,
        likes=snapshot.likes,
        comments=snapshot.comments,
        shares=snapshot.shares,
        saves=snapshot.saves,
    )


def video_snapshot_to_domain(model: VideoSnapshotModel) -> VideoSnapshot:
    return VideoSnapshot(
        video_id=VideoId(model.video_id),
        captured_at=model.captured_at,
        source=model.source,
        views=model.views,
        likes=model.likes,
        comments=model.comments,
        shares=model.shares,
        saves=model.saves,
    )


def scoring_to_domain(model: ScoringSettingsModel) -> ScoreWeights:
    return ScoreWeights(
        engagement=model.engagement,
        growth=model.growth,
        reach=model.reach,
        consistency=model.consistency,
    )


def apply_scoring(model: ScoringSettingsModel, weights: ScoreWeights) -> None:
    model.id = SCORING_ROW_ID
    model.engagement = weights.engagement
    model.growth = weights.growth
    model.reach = weights.reach
    model.consistency = weights.consistency


def audit_to_model(entry: AuditEntry) -> AuditLogModel:
    return AuditLogModel(
        id=entry.id,
        actor_id=entry.actor_id,
        actor_email=entry.actor_email,
        action=entry.action.value,
        target_type=entry.target_type,
        target_id=entry.target_id,
        target_label=entry.target_label,
        detail=json.dumps(entry.detail, ensure_ascii=False),
        occurred_at=entry.occurred_at,
    )


def audit_to_domain(model: AuditLogModel) -> AuditEntry:
    return AuditEntry(
        id=model.id,
        actor_id=model.actor_id,
        actor_email=model.actor_email,
        action=AuditAction(model.action),
        target_type=model.target_type,
        target_id=model.target_id,
        target_label=model.target_label,
        detail=json.loads(model.detail),
        occurred_at=model.occurred_at,
    )


def notification_to_model(item: Notification) -> NotificationModel:
    return NotificationModel(
        id=item.id,
        kind=item.kind.value,
        channel_id=item.channel_id,
        dedupe_key=item.dedupe_key,
        title=item.title,
        message=item.message,
        created_at=item.created_at,
        read_at=item.read_at,
    )


def notification_to_domain(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id,
        kind=NotificationKind(model.kind),
        channel_id=ChannelId(model.channel_id),
        dedupe_key=model.dedupe_key,
        title=model.title,
        message=model.message,
        created_at=model.created_at,
        read_at=model.read_at,
    )


def push_subscription_to_model(item: PushSubscription) -> PushSubscriptionModel:
    return PushSubscriptionModel(
        id=item.id,
        user_id=item.user_id,
        endpoint=item.endpoint,
        p256dh=item.p256dh,
        auth=item.auth,
        created_at=item.created_at,
    )


def push_subscription_to_domain(model: PushSubscriptionModel) -> PushSubscription:
    return PushSubscription(
        id=model.id,
        user_id=UserId(model.user_id),
        endpoint=model.endpoint,
        p256dh=model.p256dh,
        auth=model.auth,
        created_at=model.created_at,
    )
