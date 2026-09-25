from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User

if TYPE_CHECKING:
    from app.models.request import Request


class ApprovalType(StrEnum):
    MANAGER = "MANAGER"
    FINANCE = "FINANCE"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        UniqueConstraint("request_id", "approval_type", name="uq_approvals_request_stage"),
        CheckConstraint("status <> 'REJECTED' OR (comment IS NOT NULL AND length(trim(comment)) > 0)", name="ck_approvals_reject_reason"),
        CheckConstraint("(status = 'PENDING' AND decided_at IS NULL) OR (status <> 'PENDING' AND decided_at IS NOT NULL)", name="ck_approvals_decision_time"),
        CheckConstraint("approval_type <> 'MANAGER' OR approver_id IS NOT NULL", name="ck_approvals_manager_assigned"),
        CheckConstraint("status NOT IN ('APPROVED', 'REJECTED') OR approver_id IS NOT NULL", name="ck_approvals_decider_required"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id", ondelete="RESTRICT"), index=True)
    approver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    approval_type: Mapped[ApprovalType] = mapped_column(Enum(ApprovalType, name="approval_type"))
    status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus, name="approval_status"), index=True)
    comment: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approver: Mapped[User | None] = relationship()
    request: Mapped["Request"] = relationship(back_populates="approvals")
