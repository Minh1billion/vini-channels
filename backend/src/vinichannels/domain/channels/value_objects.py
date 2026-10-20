import re
from dataclasses import dataclass
from enum import StrEnum

from vinichannels.domain.shared.errors import ValidationError


class ConnectionMode(StrEnum):
    AUTHORIZED = "authorized"
    PUBLIC = "public"


class ChannelStatus(StrEnum):
    HEALTHY = "healthy"
    TOKEN_EXPIRING = "token_expiring"
    TOKEN_REVOKED = "token_revoked"
    NOT_FOUND = "not_found"
    PRIVATE = "private"
    PROVIDER_ERROR = "provider_error"


_HANDLE_PATTERN = re.compile(r"^[a-z0-9_](?:[a-z0-9_.]{0,22}[a-z0-9_])$")


@dataclass(frozen=True, slots=True)
class Handle:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().removeprefix("@").lower()
        if not _HANDLE_PATTERN.fullmatch(normalized):
            raise ValidationError(f"Handle TikTok không hợp lệ: {self.value!r}")
        object.__setattr__(self, "value", normalized)

    @property
    def display(self) -> str:
        return f"@{self.value}"

    def __str__(self) -> str:
        return self.value
