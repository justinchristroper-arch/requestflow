from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, Sequence, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.approval import Approval


class Category(StrEnum):
    HARDWARE = "HARDWARE"
    SOFTWARE = "SOFTWARE"
    ACCESS = "ACCESS"
    REPAIR_MAINTENANCE = "REPAIR_MAINTENANCE"
    OTHER = "OTHER"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RequestStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_MANAGER_APPROVAL = "PENDING_MANAGER_APPROVAL"
    PENDING_FINANCE_APPROVAL = "PENDING_FINANCE_APPROVAL"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


request_number_sequence = Sequence("request_number_seq", metadata=Base.metadata)


class Request(Base):
    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint("estimated_cost >= 0", name="ck_requests_cost_nonnegative"),
        CheckConstraint("(status IN ('PROCESSING', 'COMPLETED') AND processing_owner_id IS NOT NULL AND processing_started_at IS NOT NULL) OR (status NOT IN ('PROCESSING', 'COMPLETED') AND processing_owner_id IS NULL AND processing_started_at IS NULL)", name="ck_requests_processing_fields"),
        CheckConstraint("(status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status <> 'COMPLETED' AND completed_at IS NULL)", name="ck_requests_completion_time"),
        CheckConstraint("completed_at IS NULL OR completed_at >= processing_started_at", name="ck_requests_fulfillment_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    request_number: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    category: Mapped[Category] = mapped_column(Enum(Category, name="request_category"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    business_justification: Mapped[str] = mapped_column(Text)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    priority: Mapped[Priority] = mapped_column(Enum(Priority, name="request_priority"))
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus, name="request_status"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processing_owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requester: Mapped[User] = relationship(foreign_keys=[requester_id])
    processing_owner: Mapped[User | None] = relationship(foreign_keys=[processing_owner_id])
    approvals: Mapped[list["Approval"]] = relationship(back_populates="request", order_by="Approval.id")
