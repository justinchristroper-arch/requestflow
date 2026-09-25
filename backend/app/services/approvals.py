from fastapi import HTTPException
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Approval, ApprovalStatus, ApprovalType, Request, RequestStatus, Role, User


def pending_approvals(db: Session, user: User, offset: int, limit: int):
    conditions = [Approval.request_id == Request.id, Approval.status == ApprovalStatus.PENDING]
    if user.role == Role.MANAGER:
        conditions.extend([Approval.approval_type == ApprovalType.MANAGER, Approval.approver_id == user.id])
        scope = (Request.status == RequestStatus.PENDING_MANAGER_APPROVAL,
                 Request.requester.has(User.manager_id == user.id), Request.requester_id != user.id)
    elif user.role == Role.FINANCE:
        conditions.append(Approval.approval_type == ApprovalType.FINANCE)
        scope = (Request.status == RequestStatus.PENDING_FINANCE_APPROVAL, Request.requester_id != user.id)
    else:
        raise HTTPException(403, "Only managers and Finance have approval queues")
    filters = [*scope, exists(select(Approval.id).where(*conditions))]
    total = db.scalar(select(func.count()).select_from(Request).where(*filters))
    items = db.scalars(select(Request).where(*filters).options(selectinload(Request.requester))
                       .order_by(Request.created_at, Request.id).offset(offset).limit(limit)).all()
    return {"items": items, "total": total, "offset": offset, "limit": limit}
