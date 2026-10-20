from datetime import UTC, datetime

from vinichannels.domain.shared.errors import ValidationError


def require_aware(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValidationError(f"{name} phải có múi giờ")
    return value.astimezone(UTC)
