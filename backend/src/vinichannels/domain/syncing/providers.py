from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from vinichannels.domain.shared.errors import ValidationError


class ProviderKey(StrEnum):
    TIKTOK = "tiktok"
    SCRAPECREATORS = "scrapecreators"
    APIFY = "apify"


@dataclass(frozen=True, slots=True)
class ProviderSpec:
    key: ProviderKey
    label: str
    credential_fields: tuple[str, ...]
    default_priority: int
    requires_channel_token: bool = False
    optional_fields: tuple[str, ...] = ()


PROVIDER_SPECS: dict[ProviderKey, ProviderSpec] = {
    ProviderKey.TIKTOK: ProviderSpec(
        ProviderKey.TIKTOK,
        "TikTok for Developers",
        ("client_key", "client_secret"),
        10,
        requires_channel_token=True,
        optional_fields=("client_key", "client_secret"),
    ),
    ProviderKey.SCRAPECREATORS: ProviderSpec(
        ProviderKey.SCRAPECREATORS, "ScrapeCreators", ("api_key",), 20
    ),
    ProviderKey.APIFY: ProviderSpec(
        ProviderKey.APIFY, "Apify", ("api_token", "actor_id"), 30, optional_fields=("actor_id",)
    ),
}


def month_start(moment: datetime) -> datetime:
    return moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


@dataclass(slots=True)
class ProviderConfig:
    key: ProviderKey
    enabled: bool = False
    priority: int = 100
    monthly_quota: int | None = None
    credentials_enc: bytes | None = None

    def __post_init__(self) -> None:
        if self.monthly_quota is not None and self.monthly_quota < 0:
            raise ValidationError("Hạn mức không được âm")

    @property
    def is_configured(self) -> bool:
        spec = PROVIDER_SPECS[self.key]
        required = set(spec.credential_fields) - set(spec.optional_fields)
        return not required or self.credentials_enc is not None

    def quota_exhausted(self, used: int) -> bool:
        return self.monthly_quota is not None and used >= self.monthly_quota

    @classmethod
    def default_for(cls, key: ProviderKey) -> "ProviderConfig":
        spec = PROVIDER_SPECS[key]
        return cls(key=key, enabled=False, priority=spec.default_priority)
