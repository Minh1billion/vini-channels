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
        )
