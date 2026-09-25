from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models import AuditAction, RequestStatus
from app.schemas.auth import ManagerSummary


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_id: int
    actor: ManagerSummary | None
    action: AuditAction
    previous_status: RequestStatus | None
    new_status: RequestStatus | None
    details: str | None
    created_at: datetime
