from datetime import datetime

from pydantic import BaseModel, ConfigDict

from vinichannels.domain.audit.entities import AuditAction


class AuditEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    actor_email: str
    action: AuditAction
    target_type: str
    target_id: str
    target_label: str
    detail: dict[str, str]
    occurred_at: datetime
