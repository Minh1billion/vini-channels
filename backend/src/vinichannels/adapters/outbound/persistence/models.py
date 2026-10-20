from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class UtcDateTime(TypeDecorator[datetime]):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return None if value is None else value.astimezone(UTC)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        result = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
        return cast(datetime, result)


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    locked_until: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)


class PartnerTagModel(Base):
    __tablename__ = "partner_tags"

    partner_id: Mapped[str] = mapped_column(
        ForeignKey("partners.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)


class PartnerModel(Base):
    __tablename__ = "partners"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    archived_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    tags: Mapped[list[PartnerTagModel]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class ChannelModel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    partner_id: Mapped[str] = mapped_column(ForeignKey("partners.id"), index=True)
    platform_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    handle: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    connection_mode: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(24))
    sync_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    archived_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)


class ChannelCredentialModel(Base):
    __tablename__ = "channel_credentials"

    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), primary_key=True)
    access_token_enc: Mapped[bytes] = mapped_column(LargeBinary)
    refresh_token_enc: Mapped[bytes] = mapped_column(LargeBinary)
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    refresh_expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    scopes: Mapped[str] = mapped_column(Text, default="")


class ProviderConfigModel(Base):
    __tablename__ = "provider_configs"

    key: Mapped[str] = mapped_column(String(32), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    monthly_quota: Mapped[int | None] = mapped_column(Integer, nullable=True)
    credentials_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)


class SyncRunModel(Base):
    __tablename__ = "sync_runs"
    __table_args__ = (
        UniqueConstraint("channel_id", "scheduled_for", "trigger", name="uq_sync_runs_slot"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), index=True)
    scheduled_for: Mapped[datetime] = mapped_column(UtcDateTime)
    trigger: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)
    status: Mapped[str] = mapped_column(String(16))
    finished_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    items_fetched: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class VideoModel(Base):
    __tablename__ = "videos"
    __table_args__ = (UniqueConstraint("channel_id", "platform_video_id"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), index=True)
    platform_video_id: Mapped[str] = mapped_column(String(64))
    posted_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)
    url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    caption: Mapped[str] = mapped_column(Text, default="")
    thumbnail_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)


class ChannelSnapshotModel(Base):
    __tablename__ = "channel_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("channels.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)
    source: Mapped[str] = mapped_column(String(32))
    followers: Mapped[int] = mapped_column(BigInteger)
    following: Mapped[int] = mapped_column(BigInteger)
    total_likes: Mapped[int] = mapped_column(BigInteger)
    video_count: Mapped[int] = mapped_column(Integer)


class VideoSnapshotModel(Base):
    __tablename__ = "video_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), index=True)
    captured_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)
    source: Mapped[str] = mapped_column(String(32))
    views: Mapped[int] = mapped_column(BigInteger)
    likes: Mapped[int] = mapped_column(BigInteger)
    comments: Mapped[int] = mapped_column(BigInteger)
    shares: Mapped[int] = mapped_column(BigInteger)
    saves: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class ScoringSettingsModel(Base):
    __tablename__ = "scoring_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engagement: Mapped[float] = mapped_column(Float)
    growth: Mapped[float] = mapped_column(Float)
    reach: Mapped[float] = mapped_column(Float)
    consistency: Mapped[float] = mapped_column(Float)


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    actor_id: Mapped[str] = mapped_column(String(32), index=True)
    actor_email: Mapped[str] = mapped_column(String(320))
    action: Mapped[str] = mapped_column(String(32), index=True)
    target_type: Mapped[str] = mapped_column(String(16))
    target_id: Mapped[str] = mapped_column(String(64))
    target_label: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(Text, default="{}")
    occurred_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    kind: Mapped[str] = mapped_column(String(24), index=True)
    channel_id: Mapped[str] = mapped_column(String(32), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, index=True)
    read_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
