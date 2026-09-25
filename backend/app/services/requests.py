from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import exists, func, or_, select, true
from sqlalchemy.orm import Session, selectinload

from app.models import Approval, ApprovalStatus, ApprovalType, AuditAction, Request, RequestStatus, Role, User
from app.models.request import request_number_sequence
from app.schemas.request import RequestInput
from app.services.rules import calculate_due_date
from app.services import audit


def visibility(user: User):
    own = Request.requester_id == user.id
    if user.role == Role.ADMIN:
        return true()
    if user.role == Role.MANAGER:
        return or_(own, Request.requester.has(User.manager_id == user.id))
    if user.role == Role.FINANCE:
        return exists(select(Approval.id).where(Approval.request_id == Request.id, Approval.approval_type == ApprovalType.FINANCE))
    if user.role == Role.PROCUREMENT:
        return Request.status.in_((RequestStatus.APPROVED, RequestStatus.PROCESSING, RequestStatus.COMPLETED))
    return own


def visible_request(db: Session, request_id: int, user: User, *, lock=False) -> Request:
    query = select(Request).where(Request.id == request_id, visibility(user))
    if lock:
        query = query.with_for_update(of=Request).execution_options(populate_existing=True)
    request = db.scalar(query)
    if request is None:
        raise HTTPException(404, "Request not found")
    return request


def list_requests(db: Session, user: User, offset: int, limit: int, own: bool):
    conditions = [visibility(user)]
    if own:
        conditions.append(Request.requester_id == user.id)
    total = db.scalar(select(func.count()).select_from(Request).where(*conditions))
    items = db.scalars(select(Request).where(*conditions).options(selectinload(Request.requester))
                       .order_by(Request.created_at.desc(), Request.id.desc()).offset(offset).limit(limit)).all()
    return {"items": items, "total": total, "offset": offset, "limit": limit}


def create_request(db: Session, user: User, data: RequestInput, *, now: datetime | None = None) -> Request:
    if user.role not in (Role.EMPLOYEE, Role.MANAGER):
        raise HTTPException(403, "Only employees and managers may submit requests")
    manager = db.get(User, user.manager_id) if user.manager_id else None
    if not manager or not manager.is_active or manager.role != Role.MANAGER or manager.id == user.id:
        raise HTTPException(409, "An active manager must be assigned before you can submit a request")
    now = now if now is not None else datetime.now(timezone.utc)
    number = db.scalar(select(request_number_sequence.next_value()))
    request = Request(**data.model_dump(), requester_id=user.id,
                      request_number=f"REQ-{now.year}-{number:04d}", status=RequestStatus.PENDING_MANAGER_APPROVAL,
                      created_at=now, updated_at=now, due_date=calculate_due_date(now, data.priority))
    db.add(request)
    db.flush()
    db.add(Approval(request_id=request.id, approver_id=manager.id,
                    approval_type=ApprovalType.MANAGER, status=ApprovalStatus.PENDING, created_at=now))
    audit.record_event(db, request_id=request.id, actor_id=user.id, action=AuditAction.REQUEST_CREATED,
                       previous_status=None, new_status=request.status, created_at=now)
    return request
