from datetime import datetime, timezone
from enum import StrEnum

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Approval, ApprovalStatus, ApprovalType, AuditAction, Request, RequestStatus, Role, User
from app.schemas.request import Decision, DecisionInput, RequestDetail, RequestSummary
from app.services.requests import visible_request
from app.services.rules import FINANCE_APPROVAL_THRESHOLD, finance_required
from app.services import audit


class Action(StrEnum):
    CANCEL = "cancel"
    MANAGER_APPROVE = "manager_approve"
    MANAGER_REJECT = "manager_reject"
    FINANCE_APPROVE = "finance_approve"
    FINANCE_REJECT = "finance_reject"
    START_PROCESSING = "start_processing"
    COMPLETE = "complete"


TRANSITIONS = {
    (RequestStatus.PENDING_MANAGER_APPROVAL, Action.CANCEL): RequestStatus.CANCELLED,
    (RequestStatus.PENDING_MANAGER_APPROVAL, Action.MANAGER_APPROVE): RequestStatus.APPROVED,
    (RequestStatus.PENDING_MANAGER_APPROVAL, Action.MANAGER_REJECT): RequestStatus.REJECTED,
    (RequestStatus.PENDING_FINANCE_APPROVAL, Action.FINANCE_APPROVE): RequestStatus.APPROVED,
    (RequestStatus.PENDING_FINANCE_APPROVAL, Action.FINANCE_REJECT): RequestStatus.REJECTED,
    (RequestStatus.APPROVED, Action.START_PROCESSING): RequestStatus.PROCESSING,
    (RequestStatus.PROCESSING, Action.COMPLETE): RequestStatus.COMPLETED,
}

AUDIT_ACTIONS = {
    Action.CANCEL: AuditAction.REQUEST_CANCELLED,
    Action.MANAGER_APPROVE: AuditAction.MANAGER_APPROVED,
    Action.MANAGER_REJECT: AuditAction.MANAGER_REJECTED,
    Action.FINANCE_APPROVE: AuditAction.FINANCE_APPROVED,
    Action.FINANCE_REJECT: AuditAction.FINANCE_REJECTED,
    Action.START_PROCESSING: AuditAction.PROCESSING_STARTED,
    Action.COMPLETE: AuditAction.REQUEST_COMPLETED,
}


def next_status(status: RequestStatus, action: Action, cost) -> RequestStatus:
    result = TRANSITIONS.get((status, action))
    if result is None:
        raise HTTPException(409, "This action is no longer available for the current request status")
    if action == Action.MANAGER_APPROVE and finance_required(cost):
        return RequestStatus.PENDING_FINANCE_APPROVAL
    return result


def assigned_manager(request: Request, user: User) -> bool:
    return (user.role == Role.MANAGER and user.id != request.requester_id
            and request.requester.manager_id == user.id
            and any(a.approval_type == ApprovalType.MANAGER and a.approver_id == user.id
                    for a in request.approvals))


def allowed_actions(request: Request, user: User) -> list[str]:
    actions = []
    if request.status == RequestStatus.PENDING_MANAGER_APPROVAL:
        if request.requester_id == user.id:
            actions.append("cancel")
        if assigned_manager(request, user):
            actions.extend(["manager_approve", "manager_reject"])
    elif request.status == RequestStatus.PENDING_FINANCE_APPROVAL and user.role == Role.FINANCE and user.id != request.requester_id:
        actions.extend(["finance_approve", "finance_reject"])
    elif user.role == Role.PROCUREMENT:
        if request.status == RequestStatus.APPROVED:
            actions.append(Action.START_PROCESSING.value)
        elif request.status == RequestStatus.PROCESSING and request.processing_owner_id == user.id:
            actions.append(Action.COMPLETE.value)
    return actions


def detail(request: Request, user: User) -> RequestDetail:
    return RequestDetail(**RequestSummary.model_validate(request).model_dump(),
                         description=request.description, business_justification=request.business_justification,
                         finance_required=finance_required(request.estimated_cost), approvals=request.approvals,
                         processing_owner=request.processing_owner, processing_started_at=request.processing_started_at,
                         allowed_actions=allowed_actions(request, user))


def transition(db: Session, request_id: int, user: User, action: Action, decision: DecisionInput | None = None,
               *, note: str | None = None, now: datetime | None = None) -> Request:
    # All competing decisions/cancellations serialize on this row until commit.
    request = visible_request(db, request_id, user, lock=True)
    if action in (Action.START_PROCESSING, Action.COMPLETE):
        return fulfill(db, request, user, action, note, now=now)
    if action == Action.CANCEL:
        if request.requester_id != user.id:
            raise HTTPException(403, "Only the requester can cancel this request")
        stage = ApprovalType.MANAGER
    elif action in (Action.MANAGER_APPROVE, Action.MANAGER_REJECT):
        if not assigned_manager(request, user):
            raise HTTPException(403, "Only the assigned manager can decide this approval")
        stage = ApprovalType.MANAGER
    else:
        if user.role != Role.FINANCE or user.id == request.requester_id:
            raise HTTPException(403, "Only Finance may decide this approval")
        stage = ApprovalType.FINANCE
    destination = next_status(request.status, action, request.estimated_cost)
    previous_status = request.status
    approval = db.scalar(select(Approval).where(Approval.request_id == request.id, Approval.approval_type == stage)
                         .execution_options(populate_existing=True))
    if not approval or approval.status != ApprovalStatus.PENDING:
        raise HTTPException(409, "No pending approval exists for this stage")
    now = now if now is not None else datetime.now(timezone.utc)
    if action == Action.CANCEL:
        approval.status = ApprovalStatus.CANCELLED
        approval.comment = "Cancelled by requester before review."
    else:
        if decision is None:
            raise HTTPException(422, "An approval decision is required")
        approval.status = ApprovalStatus.REJECTED if decision.decision == Decision.REJECT else ApprovalStatus.APPROVED
        approval.approver_id = user.id
        approval.comment = decision.comment or None
    approval.decided_at = now
    request.status = destination
    request.updated_at = now
    if destination == RequestStatus.PENDING_FINANCE_APPROVAL:
        db.add(Approval(request_id=request.id, approval_type=ApprovalType.FINANCE,
                        status=ApprovalStatus.PENDING, approver_id=None, created_at=now))
    db.flush()
    audit.record_event(db, request_id=request.id, actor_id=user.id, action=AUDIT_ACTIONS[action],
                       previous_status=previous_status, new_status=destination, created_at=now,
                       details=decision.comment or None if decision else None)
    if destination == RequestStatus.PENDING_FINANCE_APPROVAL:
        audit.record_event(db, request_id=request.id, actor_id=None, action=AuditAction.FINANCE_APPROVAL_REQUIRED,
                           previous_status=None, new_status=None, created_at=now,
                           details=f"Finance approval required: estimated cost IDR {request.estimated_cost:,.2f} is at or above the threshold IDR {FINANCE_APPROVAL_THRESHOLD:,.2f}.")
    # Reload collection so the response includes a newly created Finance stage.
    db.expire(request, ["approvals"])
    return request


def fulfill(db: Session, request: Request, user: User, action: Action, note: str | None, *, now: datetime | None = None) -> Request:
    """Called only after transition() obtains the common request row lock."""
    if user.role != Role.PROCUREMENT:
        raise HTTPException(403, "Only Procurement may perform fulfillment actions")
    destination = next_status(request.status, action, request.estimated_cost)
    if action == Action.COMPLETE and request.processing_owner_id != user.id:
        raise HTTPException(403, "Only the assigned processing owner can complete this request")
    previous_status = request.status
    now = now if now is not None else datetime.now(timezone.utc)
    if action == Action.START_PROCESSING:
        request.processing_owner_id = user.id
        request.processing_started_at = now
    else:
        request.completed_at = now
    request.status = destination
    request.updated_at = now
    audit.record_event(db, request_id=request.id, actor_id=user.id, action=AUDIT_ACTIONS[action],
                       previous_status=previous_status, new_status=destination, created_at=now, details=note or None)
    db.expire(request, ["processing_owner"])
    return request
