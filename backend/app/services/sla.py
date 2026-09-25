"""Read-time SLA rules; Python and SQL share the same ordered decision table."""
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import and_, case

from app.models import Request, RequestStatus

DUE_SOON_WINDOW = timedelta(hours=24)


class SLAStatus(StrEnum):
    ON_TRACK = "ON_TRACK"
    DUE_SOON = "DUE_SOON"
    BREACHED = "BREACHED"
    COMPLETED_ON_TIME = "COMPLETED_ON_TIME"
    COMPLETED_LATE = "COMPLETED_LATE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def utc_now():
    return datetime.now(timezone.utc)


def conditions(status, due, completed, now, *, sql=False):
    both = and_ if sql else lambda a, b: a and b
    # Completed timestamps are mandatory in the database. Guard Python None too.
    on_time = completed <= due if sql or completed is not None else False
    return [
        (status == RequestStatus.CANCELLED, SLAStatus.NOT_APPLICABLE),
        (status == RequestStatus.REJECTED, SLAStatus.NOT_APPLICABLE),
        (status == RequestStatus.DRAFT, SLAStatus.NOT_APPLICABLE),
        (both(status == RequestStatus.COMPLETED, on_time), SLAStatus.COMPLETED_ON_TIME),
        (status == RequestStatus.COMPLETED, SLAStatus.COMPLETED_LATE),
        (due < now, SLAStatus.BREACHED),
        (due <= now + DUE_SOON_WINDOW, SLAStatus.DUE_SOON),
    ]


def calculate(status, due_date, completed_at=None, *, now=None) -> SLAStatus:
    now = now if now is not None else utc_now()
    for value in (due_date, completed_at, now):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("SLA calculations require timezone-aware timestamps")
    if status == RequestStatus.COMPLETED and completed_at is None:
        raise ValueError("Completed requests require completed_at")
    return next((result for match, result in conditions(status, due_date, completed_at, now) if match), SLAStatus.ON_TRACK)


def sql_status(now):
    return case(*[(condition, result.value) for condition, result in conditions(
        Request.status, Request.due_date, Request.completed_at, now, sql=True)], else_=SLAStatus.ON_TRACK.value)


def urgency_order(now):
    state = sql_status(now)
    return case((state == SLAStatus.BREACHED.value, 0), (state == SLAStatus.DUE_SOON.value, 1), else_=2)


def compliance(on_time: int, completed: int):
    return round(100 * on_time / completed, 2) if completed else None
