from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import AuditAction, AuditLog, RequestStatus, User


def record_event(db: Session, *, request_id: int, actor_id: int | None, action: AuditAction,
                 previous_status: RequestStatus | None, new_status: RequestStatus | None,
                 created_at: datetime, details: str | None = None) -> AuditLog:
    """Append within the caller's transaction; never independently commit audit data."""
    event = AuditLog(request_id=request_id, actor_id=actor_id, action=action,
                     previous_status=previous_status, new_status=new_status, details=details, created_at=created_at)
    db.add(event)
    db.flush()
    return event


def request_history(db: Session, request_id: int, user: User):
    from app.services.requests import visible_request
    visible_request(db, request_id, user)
    return db.scalars(select(AuditLog).where(AuditLog.request_id == request_id)
                      .options(selectinload(AuditLog.actor)).order_by(AuditLog.created_at, AuditLog.id)).all()
