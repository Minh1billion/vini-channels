from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_configs",
        sa.Column("key", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("monthly_quota", sa.Integer(), nullable=True),
        sa.Column("credentials_enc", sa.LargeBinary(), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)

    op.create_table(
        "partners",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("owner_user_id", sa.String(length=32), nullable=True),
        sa.Column("logo_url", sa.String(length=1000), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "channels",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("partner_id", sa.String(length=32), nullable=False),
        sa.Column("platform_channel_id", sa.String(length=64), nullable=True),
        sa.Column("handle", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("avatar_url", sa.String(length=1000), nullable=True),
        sa.Column("connection_mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("sync_cron", sa.String(length=100), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["partner_id"],
            ["partners.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("channels", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_channels_handle"), ["handle"], unique=True)
        batch_op.create_index(batch_op.f("ix_channels_partner_id"), ["partner_id"], unique=False)

    op.create_table(
        "partner_tags",
        sa.Column("partner_id", sa.String(length=32), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["partners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("partner_id", "tag"),
    )
    with op.batch_alter_table("partner_tags", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_partner_tags_tag"), ["tag"], unique=False)

    op.create_table(
        "channel_credentials",
        sa.Column("channel_id", sa.String(length=32), nullable=False),
        sa.Column("access_token_enc", sa.LargeBinary(), nullable=False),
        sa.Column("refresh_token_enc", sa.LargeBinary(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refresh_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channels.id"],
        ),
        sa.PrimaryKeyConstraint("channel_id"),
    )
    op.create_table(
        "channel_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("channel_id", sa.String(length=32), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("followers", sa.BigInteger(), nullable=False),
        sa.Column("following", sa.BigInteger(), nullable=False),
        sa.Column("total_likes", sa.BigInteger(), nullable=False),
        sa.Column("video_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channels.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("channel_snapshots", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_channel_snapshots_captured_at"), ["captured_at"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_channel_snapshots_channel_id"), ["channel_id"], unique=False
        )

    op.create_table(
        "sync_runs",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("channel_id", sa.String(length=32), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trigger", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("items_fetched", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channels.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("sync_runs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_sync_runs_channel_id"), ["channel_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_sync_runs_source"), ["source"], unique=False)
        batch_op.create_index(batch_op.f("ix_sync_runs_started_at"), ["started_at"], unique=False)

    op.create_table(
        "videos",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("channel_id", sa.String(length=32), nullable=False),
        sa.Column("platform_video_id", sa.String(length=64), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=1000), nullable=True),
        sa.Column("duration_sec", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channels.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_id", "platform_video_id"),
    )
    with op.batch_alter_table("videos", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_videos_channel_id"), ["channel_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_videos_posted_at"), ["posted_at"], unique=False)

    op.create_table(
        "video_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("video_id", sa.String(length=32), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("views", sa.BigInteger(), nullable=False),
        sa.Column("likes", sa.BigInteger(), nullable=False),
        sa.Column("comments", sa.BigInteger(), nullable=False),
        sa.Column("shares", sa.BigInteger(), nullable=False),
        sa.Column("saves", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("video_snapshots", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_video_snapshots_captured_at"), ["captured_at"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_video_snapshots_video_id"), ["video_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("video_snapshots", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_video_snapshots_video_id"))
        batch_op.drop_index(batch_op.f("ix_video_snapshots_captured_at"))

    op.drop_table("video_snapshots")
    with op.batch_alter_table("videos", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_videos_posted_at"))
        batch_op.drop_index(batch_op.f("ix_videos_channel_id"))

    op.drop_table("videos")
    with op.batch_alter_table("sync_runs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_sync_runs_started_at"))
        batch_op.drop_index(batch_op.f("ix_sync_runs_source"))
        batch_op.drop_index(batch_op.f("ix_sync_runs_channel_id"))

    op.drop_table("sync_runs")
    with op.batch_alter_table("channel_snapshots", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_channel_snapshots_channel_id"))
        batch_op.drop_index(batch_op.f("ix_channel_snapshots_captured_at"))

    op.drop_table("channel_snapshots")
    op.drop_table("channel_credentials")
    with op.batch_alter_table("partner_tags", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_partner_tags_tag"))

    op.drop_table("partner_tags")
    with op.batch_alter_table("channels", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_channels_partner_id"))
        batch_op.drop_index(batch_op.f("ix_channels_handle"))

    op.drop_table("channels")
    op.drop_table("partners")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email"))

    op.drop_table("users")
    op.drop_table("provider_configs")
