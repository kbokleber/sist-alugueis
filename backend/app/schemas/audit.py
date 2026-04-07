from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    old_values: dict | None = None
    new_values: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime
