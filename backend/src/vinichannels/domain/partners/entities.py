from dataclasses import dataclass, field
from datetime import datetime

from vinichannels.domain.shared.errors import InvalidStateError, ValidationError
from vinichannels.domain.shared.ids import PartnerId, UserId


@dataclass(slots=True)
class Partner:
    id: PartnerId
    name: str
    industry: str | None = None
    owner_user_id: UserId | None = None
    logo_url: str | None = None
    notes: str = ""
    tags: frozenset[str] = field(default_factory=frozenset)
    archived_at: datetime | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValidationError("Tên đối tác không được để trống")

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def rename(self, name: str) -> None:
        clean = name.strip()
        if not clean:
            raise ValidationError("Tên đối tác không được để trống")
        self.name = clean

    def add_tag(self, tag: str) -> None:
        clean = tag.strip().lower()
        if not clean:
            raise ValidationError("Nhãn không được để trống")
        self.tags = self.tags | {clean}

    def remove_tag(self, tag: str) -> None:
        self.tags = self.tags - {tag.strip().lower()}

    def archive(self, at: datetime) -> None:
        if self.is_archived:
            raise InvalidStateError("Đối tác đã được lưu trữ")
        self.archived_at = at

    def restore(self) -> None:
        if not self.is_archived:
            raise InvalidStateError("Đối tác chưa được lưu trữ")
        self.archived_at = None
