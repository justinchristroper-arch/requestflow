from datetime import datetime
from pydantic import BaseModel


class Bucket(BaseModel):
    key: str
    count: int


class KPIs(BaseModel):
    total_requests: int
    pending_approval: int
    processing: int
    completed: int
    rejected: int
    completed_on_time: int
    sla_compliance_percent: float | None
    average_resolution_hours: float | None


class AnalyticsResponse(BaseModel):
    as_of: datetime
    timezone: str
    kpis: KPIs
    by_category: list[Bucket]
    by_priority: list[Bucket]
    by_status: list[Bucket]
    by_sla: list[Bucket]
    monthly_trend: list[Bucket]
