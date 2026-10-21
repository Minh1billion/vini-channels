import os
import secrets
from dataclasses import dataclass, field

from vinichannels.adapters.outbound.persistence.database import (
    DEFAULT_DATABASE_URL,
    normalize_database_url,
)


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    secret_key: str = field(default_factory=lambda: secrets.token_urlsafe(48))
    session_ttl_hours: int = 12
    cookie_secure: bool = False
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)
    admin_email: str | None = None
    admin_password: str | None = None
    scheduler_interval_sec: float = 30.0
    scheduler_concurrency: int = 3
    sync_lookback_days: int = 30
    sync_max_videos: int = 100
    sync_max_pages: int = 10
    backfill_max_pages: int = 100
    minio_endpoint: str | None = None
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "vini-thumbnails"
    minio_secure: bool = False
    vapid_public_key: str | None = None
    vapid_private_key: str | None = None
    vapid_subject: str = "mailto:admin@vini.local"

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ
        defaults = cls()
        origins = env.get("VINI_CORS_ORIGINS")
        return cls(
            database_url=normalize_database_url(
                env.get("VINI_DATABASE_URL", defaults.database_url)
            ),
            secret_key=env.get("VINI_SECRET_KEY") or defaults.secret_key,
            session_ttl_hours=int(env.get("VINI_SESSION_TTL_HOURS", defaults.session_ttl_hours)),
            cookie_secure=_flag(env.get("VINI_COOKIE_SECURE")),
            cors_origins=(
                tuple(item.strip() for item in origins.split(",") if item.strip())
                if origins is not None
                else defaults.cors_origins
            ),
            admin_email=env.get("VINI_ADMIN_EMAIL") or None,
            admin_password=env.get("VINI_ADMIN_PASSWORD") or None,
            scheduler_interval_sec=float(
                env.get("VINI_SCHEDULER_INTERVAL_SEC", defaults.scheduler_interval_sec)
            ),
            scheduler_concurrency=int(
                env.get("VINI_SCHEDULER_CONCURRENCY", defaults.scheduler_concurrency)
            ),
            sync_lookback_days=int(env.get("VINI_SYNC_LOOKBACK_DAYS", defaults.sync_lookback_days)),
            sync_max_videos=int(env.get("VINI_SYNC_MAX_VIDEOS", defaults.sync_max_videos)),
            sync_max_pages=int(env.get("VINI_SYNC_MAX_PAGES", defaults.sync_max_pages)),
            backfill_max_pages=int(env.get("VINI_BACKFILL_MAX_PAGES", defaults.backfill_max_pages)),
            minio_endpoint=env.get("VINI_MINIO_ENDPOINT") or None,
            minio_access_key=env.get("VINI_MINIO_ACCESS_KEY", defaults.minio_access_key),
            minio_secret_key=env.get("VINI_MINIO_SECRET_KEY", defaults.minio_secret_key),
            minio_bucket=env.get("VINI_MINIO_BUCKET") or defaults.minio_bucket,
            minio_secure=_flag(env.get("VINI_MINIO_SECURE")),
            vapid_public_key=env.get("VINI_VAPID_PUBLIC_KEY") or None,
            vapid_private_key=env.get("VINI_VAPID_PRIVATE_KEY") or None,
            vapid_subject=env.get("VINI_VAPID_SUBJECT") or defaults.vapid_subject,
        )
