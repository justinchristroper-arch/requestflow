from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_user, get_db
from app.models import RequestStatus, User
from app.schemas.request import Decision, DecisionInput, FulfillmentInput, RequestDetail, RequestInput, RequestPage
from app.schemas.audit import AuditResponse
from app.services import requests, workflow
from app.services.approvals import pending_approvals
from app.services import audit, procurement

router = APIRouter(tags=["Requests and approvals"])
DB = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(get_current_active_user)]
RequestId = Annotated[int, Path(gt=0, le=2147483647)]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.post("/requests", response_model=RequestDetail, status_code=201)
def create(payload: RequestInput, db: DB, user: Actor):
    request = requests.create_request(db, user, payload)
    result = workflow.detail(request, user)
    db.commit()
    return result


@router.get("/requests", response_model=RequestPage)
def list_visible(db: DB, user: Actor, offset: Offset = 0, limit: Limit = 20, own: bool = False):
    return requests.list_requests(db, user, offset, limit, own)


@router.get("/requests/{request_id}", response_model=RequestDetail)
def get_detail(request_id: RequestId, db: DB, user: Actor):
    return workflow.detail(requests.visible_request(db, request_id, user), user)


@router.patch("/requests/{request_id}/cancel", response_model=RequestDetail)
def cancel(request_id: RequestId, db: DB, user: Actor):
    request = workflow.transition(db, request_id, user, workflow.Action.CANCEL)
    result = workflow.detail(request, user)
    db.commit()
    return result


@router.post("/requests/{request_id}/manager-approval", response_model=RequestDetail)
def manager_decision(request_id: RequestId, payload: DecisionInput, db: DB, user: Actor):
    action = workflow.Action.MANAGER_APPROVE if payload.decision == Decision.APPROVE else workflow.Action.MANAGER_REJECT
    request = workflow.transition(db, request_id, user, action, payload)
    result = workflow.detail(request, user)
    db.commit()
    return result


@router.post("/requests/{request_id}/finance-approval", response_model=RequestDetail)
def finance_decision(request_id: RequestId, payload: DecisionInput, db: DB, user: Actor):
    action = workflow.Action.FINANCE_APPROVE if payload.decision == Decision.APPROVE else workflow.Action.FINANCE_REJECT
    request = workflow.transition(db, request_id, user, action, payload)
    result = workflow.detail(request, user)
    db.commit()
    return result


@router.get("/approvals/pending", response_model=RequestPage)
def pending(db: DB, user: Actor, offset: Offset = 0, limit: Limit = 20):
    return pending_approvals(db, user, offset, limit)


@router.get("/procurement/queue", response_model=RequestPage)
def procurement_queue(db: DB, user: Actor, offset: Offset = 0, limit: Limit = 20, status: RequestStatus | None = None):
    return procurement.queue(db, user, offset, limit, status)


@router.post("/requests/{request_id}/start-processing", response_model=RequestDetail)
def start_processing(request_id: RequestId, payload: FulfillmentInput, db: DB, user: Actor):
    request = workflow.transition(db, request_id, user, workflow.Action.START_PROCESSING, note=payload.note)
    result = workflow.detail(request, user)
    db.commit()
    return result


@router.post("/requests/{request_id}/complete", response_model=RequestDetail)
def complete(request_id: RequestId, payload: FulfillmentInput, db: DB, user: Actor):
    request = workflow.transition(db, request_id, user, workflow.Action.COMPLETE, note=payload.note)
    result = workflow.detail(request, user)
    db.commit()
    return result


@router.get("/requests/{request_id}/audit", response_model=list[AuditResponse])
def history(request_id: RequestId, db: DB, user: Actor):
    return audit.request_history(db, request_id, user)
