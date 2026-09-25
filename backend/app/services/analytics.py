from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, Priority, Request, RequestStatus
from app.services import sla

REPORT_TIMEZONE = "Asia/Jakarta"


def dashboard(db: Session, *, now=None):
    now = now if now is not None else sla.utc_now()
    # One aggregate statement yields a consistent PostgreSQL snapshot for all metrics.
    def counts(expression, name):
        grouped = select(expression.label("key"), func.count().label("count")).select_from(Request).group_by(expression).subquery()
        return select(func.json_object_agg(grouped.c.key, grouped.c.count)).scalar_subquery().label(name)

    completed = Request.status == RequestStatus.COMPLETED
    completed_count = func.count().filter(completed)
    on_time = func.count().filter(completed, Request.completed_at <= Request.due_date)
    average = func.avg(func.extract("epoch", Request.completed_at - Request.created_at) / 3600).filter(completed)
    local_now = now.astimezone(ZoneInfo(REPORT_TIMEZONE))
    current_index = local_now.year * 12 + local_now.month - 1
    months = [f"{index // 12:04d}-{index % 12 + 1:02d}" for index in range(current_index - 5, current_index + 1)]
    month = func.to_char(func.timezone(REPORT_TIMEZONE, Request.created_at), "YYYY-MM")
    monthly = select(month.label("month"), func.count().label("count")).where(month.in_(months)).group_by(month).subquery()
    row = db.execute(select(
        func.count().label("total"), completed_count.label("completed"), on_time.label("on_time"), average.label("average"),
        counts(Request.category, "categories"), counts(Request.priority, "priorities"),
        counts(Request.status, "statuses"), counts(sla.sql_status(now), "sla_states"),
        select(func.json_object_agg(monthly.c.month, monthly.c.count)).scalar_subquery().label("months"),
    ).select_from(Request)).one()
    statuses = row.statuses or {}
    def buckets(values, data):
        return [{"key": str(value), "count": (data or {}).get(str(value), 0)} for value in values]
    return {
        "as_of": now, "timezone": REPORT_TIMEZONE,
        "kpis": {"total_requests": row.total, "pending_approval": statuses.get("PENDING_MANAGER_APPROVAL", 0) + statuses.get("PENDING_FINANCE_APPROVAL", 0),
                 "processing": statuses.get("PROCESSING", 0), "completed": row.completed, "rejected": statuses.get("REJECTED", 0),
                 "completed_on_time": row.on_time, "sla_compliance_percent": sla.compliance(row.on_time, row.completed),
                 "average_resolution_hours": round(float(row.average), 2) if row.average is not None else None},
        "by_category": buckets(Category, row.categories), "by_priority": buckets(Priority, row.priorities),
        "by_status": buckets(RequestStatus, statuses), "by_sla": buckets(sla.SLAStatus, row.sla_states),
        "monthly_trend": buckets(months, row.months),
    }
