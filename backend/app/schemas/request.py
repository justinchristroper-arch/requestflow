from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.models import Category, Priority, RequestStatus, ApprovalType, ApprovalStatus
from app.schemas.auth import ManagerSummary
from app.services import sla


class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    category: Category
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=10000)
    business_justification: str = Field(min_length=1, max_length=5000)
    estimated_cost: Decimal = Field(ge=0, max_digits=15, decimal_places=2, allow_inf_nan=False)
    priority: Priority

    @field_validator("estimated_cost", mode="before")
    @classmethod
    def exact_money(cls, value):
        if isinstance(value, (float, bool)):
            raise ValueError("Send estimated_cost as an exact decimal string, for example '2000000.00'")
        return value


class Decision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class DecisionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    decision: Decision
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def rejection_reason(self):
        if self.decision == Decision.REJECT and not self.comment:
            raise ValueError("A rejection reason is required")
        return self


class FulfillmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    note: str | None = Field(default=None, max_length=2000)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    approval_type: ApprovalType
    status: ApprovalStatus
    approver: ManagerSummary | None
    comment: str | None
    created_at: datetime
    decided_at: datetime | None


class RequestSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_number: str
    requester: ManagerSummary
    category: Category
    title: str
    estimated_cost: Decimal
    priority: Priority
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    due_date: datetime
    completed_at: datetime | None

    @computed_field
    @property
    def sla_status(self) -> sla.SLAStatus:
        return sla.calculate(self.status, self.due_date, self.completed_at)


class RequestDetail(RequestSummary):
    processing_owner: ManagerSummary | None
    processing_started_at: datetime | None
    description: str
    business_justification: str
    finance_required: bool
    approvals: list[ApprovalResponse]
    allowed_actions: list[str]


class RequestPage(BaseModel):
    items: list[RequestSummary]
    total: int
    offset: int
    limit: int
