from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Priority, Request, RequestStatus, Role, User
from app.services import sla


def queue(db: Session, user: User, offset: int, limit: int, status: RequestStatus | None):
    if user.role != Role.PROCUREMENT:
        raise HTTPException(403, "Only Procurement may view the fulfillment queue")
    eligible = (RequestStatus.APPROVED, RequestStatus.PROCESSING)
    if status is not None and status not in eligible:
        raise HTTPException(422, "Queue status must be APPROVED or PROCESSING")
    scope = Request.status == status if status else Request.status.in_(eligible)
    priority_order = case((Request.priority == Priority.HIGH, 0), (Request.priority == Priority.MEDIUM, 1), else_=2)
    total = db.scalar(select(func.count()).select_from(Request).where(scope))
    items = db.scalars(select(Request).where(scope).options(selectinload(Request.requester))
                       .order_by(sla.urgency_order(sla.utc_now()), priority_order, Request.due_date, Request.created_at, Request.id)
                       .offset(offset).limit(limit)).all()
    return {"items": items, "total": total, "offset": offset, "limit": limit}
