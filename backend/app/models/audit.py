from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.request import RequestStatus
from app.models.user import User


class AuditAction(StrEnum):
    REQUEST_CREATED = "REQUEST_CREATED"
    REQUEST_CANCELLED = "REQUEST_CANCELLED"
    MANAGER_APPROVED = "MANAGER_APPROVED"
    MANAGER_REJECTED = "MANAGER_REJECTED"
    FINANCE_APPROVAL_REQUIRED = "FINANCE_APPROVAL_REQUIRED"
    FINANCE_APPROVED = "FINANCE_APPROVED"
    FINANCE_REJECTED = "FINANCE_REJECTED"
    PROCESSING_STARTED = "PROCESSING_STARTED"
    REQUEST_COMPLETED = "REQUEST_COMPLETED"
    HISTORY_BASELINE = "HISTORY_BASELINE"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_request_order", "request_id", "created_at", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="RESTRICT"))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction, name="audit_action"))
    previous_status: Mapped[RequestStatus | None] = mapped_column(Enum(RequestStatus, name="request_status"))
    new_status: Mapped[RequestStatus | None] = mapped_column(Enum(RequestStatus, name="request_status"))
    details: Mapped[str | None] = mapped_column(String(3000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor: Mapped[User | None] = relationship()
