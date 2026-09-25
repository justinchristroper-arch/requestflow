from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password
from app.config import Settings
from app.models import Approval, ApprovalStatus, ApprovalType, Request, RequestStatus, Role, User
from app.schemas.request import Decision, DecisionInput
from app.services import workflow
from app.services.workflow import Action, next_status


PAYLOAD = {"category": "HARDWARE", "title": "Workstation monitor", "description": "A second monitor for support tasks.",
           "business_justification": "Reduce window switching during incident triage.", "estimated_cost": "2000000.00", "priority": "MEDIUM"}


@pytest.fixture
def actors(seeded):
    users = {user.role.value: user for user in seeded.scalars(select(User))}
    other_manager = User(name="Other manager", email="other.manager@requestflow.demo", role=Role.MANAGER,
                         hashed_password=hash_password("Other-password"))
    seeded.add(other_manager)
    seeded.flush()
    other = User(name="Other employee", email="other.employee@requestflow.demo", role=Role.EMPLOYEE,
                 manager_id=other_manager.id, hashed_password=hash_password("Other-password"))
    seeded.add(other)
    seeded.commit()
    users.update(OTHER=other, OTHER_MANAGER=other_manager)
    return users


def headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.id, Settings())}"}


def submit(client, actors, role="EMPLOYEE", **overrides):
    return client.post("/requests", headers=headers(actors[role]), json={**PAYLOAD, **overrides})


def decide(client, actors, request_id, role="MANAGER", stage="manager", decision="APPROVE", comment=None):
    return client.post(f"/requests/{request_id}/{stage}-approval", headers=headers(actors[role]),
                       json={"decision": decision, "comment": comment})


def test_creation_ownership_number_and_approval(client, actors):
    response = submit(client, actors)
    assert response.status_code == 201
    item = response.json()
    assert item["requester"]["id"] == actors["EMPLOYEE"].id
    assert item["request_number"].startswith(f"REQ-{datetime.now().year}-")
    assert item["status"] == "PENDING_MANAGER_APPROVAL"
    assert Decimal(item["estimated_cost"]) == Decimal("2000000.00")
    assert item["approvals"][0]["approver"]["id"] == actors["MANAGER"].id
    assert item["approvals"][0]["status"] == "PENDING"
    assert item["allowed_actions"] == ["cancel"]
    assert "hashed_password" not in response.text
    second = submit(client, actors).json()
    assert item["request_number"] != second["request_number"]


@pytest.mark.parametrize("field,value", [("requester_id", 99), ("status", "APPROVED"), ("request_number", "SPOOF"),
    ("due_date", "2030-01-01"), ("created_at", "2030-01-01"), ("estimated_cost", "-1"), ("estimated_cost", "1.001"),
    ("estimated_cost", 12.34), ("estimated_cost", "NaN"), ("title", "   "), ("title", "x"*161),
    ("description", ""), ("business_justification", " "), ("category", "INVALID"), ("priority", "URGENT")])
def test_invalid_input_and_spoofing(client, actors, field, value):
    assert submit(client, actors, **{field: value}).status_code == 422


@pytest.mark.parametrize("priority,days", [("HIGH", 1), ("MEDIUM", 3), ("LOW", 5)])
def test_due_dates(client, actors, priority, days):
    item = submit(client, actors, priority=priority).json()
    assert datetime.fromisoformat(item["due_date"]) - datetime.fromisoformat(item["created_at"]) == timedelta(days=days)


def test_missing_auth_and_disallowed_creators(client, actors):
    assert client.post("/requests", json=PAYLOAD).status_code == 401
    for role in ("ADMIN", "FINANCE", "PROCUREMENT"):
        assert submit(client, actors, role).status_code == 403
    assert submit(client, actors, "MANAGER").status_code == 409  # top-level manager has no manager


def test_manager_can_submit_when_assigned_and_inactive_manager_blocks(client, actors, db):
    actors["MANAGER"].manager_id = actors["OTHER_MANAGER"].id
    db.commit()
    item = submit(client, actors, "MANAGER")
    assert item.status_code == 201
    assert item.json()["approvals"][0]["approver"]["id"] == actors["OTHER_MANAGER"].id
    actors["MANAGER"].is_active = False
    db.commit()
    assert submit(client, actors).status_code == 409


def test_visibility_list_detail_and_pagination(client, actors):
    own = submit(client, actors).json()
    other = submit(client, actors, "OTHER").json()
    for role in ("EMPLOYEE", "MANAGER"):
        result = client.get("/requests", headers=headers(actors[role])).json()
        assert [r["id"] for r in result["items"]] == [own["id"]]
        assert client.get(f'/requests/{own["id"]}', headers=headers(actors[role])).status_code == 200
        assert client.get(f'/requests/{other["id"]}', headers=headers(actors[role])).status_code == 404
    assert client.get("/requests", headers=headers(actors["ADMIN"])).json()["total"] == 2
    page = client.get("/requests?limit=1&offset=1", headers=headers(actors["ADMIN"])).json()
    assert len(page["items"]) == 1 and page["total"] == 2
    assert client.get("/requests?own=true", headers=headers(actors["MANAGER"])).json()["total"] == 0
    for role in ("FINANCE", "PROCUREMENT"):
        assert client.get("/requests", headers=headers(actors[role])).json()["items"] == []


@pytest.mark.parametrize("cost,status,count", [("4999999.99", "APPROVED", 1), ("5000000.00", "PENDING_FINANCE_APPROVAL", 2), ("10000000", "PENDING_FINANCE_APPROVAL", 2)])
def test_manager_routing_boundary_and_duplicate_decision(client, actors, cost, status, count):
    item = submit(client, actors, estimated_cost=cost).json()
    result = decide(client, actors, item["id"])
    assert result.status_code == 200
    assert result.json()["status"] == status
    assert len(result.json()["approvals"]) == count
    assert decide(client, actors, item["id"]).status_code == 409
    assert client.get("/approvals/pending", headers=headers(actors["MANAGER"])).json()["items"] == []


def test_unauthorized_decisions_and_queues(client, actors):
    item = submit(client, actors).json()
    for role, code in (("EMPLOYEE", 403), ("OTHER_MANAGER", 404), ("ADMIN", 403)):
        assert decide(client, actors, item["id"], role).status_code == code
    assert client.get("/approvals/pending", headers=headers(actors["MANAGER"])).json()["items"][0]["id"] == item["id"]
    assert client.get("/approvals/pending", headers=headers(actors["OTHER_MANAGER"])).json()["items"] == []
    for role in ("ADMIN", "EMPLOYEE", "PROCUREMENT"):
        assert client.get("/approvals/pending", headers=headers(actors[role])).status_code == 403


@pytest.mark.parametrize("stage", ["manager", "finance"])
def test_rejection_requires_reason_and_stops_workflow(client, actors, stage):
    item = submit(client, actors, estimated_cost="10000000").json()
    if stage == "finance":
        decide(client, actors, item["id"])
    role = stage.upper()
    assert decide(client, actors, item["id"], role, stage, "REJECT", "  ").status_code == 422
    result = decide(client, actors, item["id"], role, stage, "REJECT", "Budget not justified.")
    assert result.status_code == 200 and result.json()["status"] == "REJECTED"
    assert result.json()["approvals"][-1]["comment"] == "Budget not justified."
    assert decide(client, actors, item["id"], role, stage).status_code == 409
    assert client.patch(f'/requests/{item["id"]}/cancel', headers=headers(actors["EMPLOYEE"])).status_code == 409


def test_finance_workflow_and_historical_visibility(client, actors):
    item = submit(client, actors, estimated_cost="10000000").json()
    assert decide(client, actors, item["id"], "FINANCE", "finance").status_code == 404
    assert client.get("/approvals/pending", headers=headers(actors["FINANCE"])).json()["items"] == []
    decide(client, actors, item["id"])
    pending = client.get("/approvals/pending", headers=headers(actors["FINANCE"])).json()
    assert pending["items"][0]["id"] == item["id"]
    for role in ("EMPLOYEE", "MANAGER", "ADMIN"):
        assert decide(client, actors, item["id"], role, "finance").status_code == 403
    result = decide(client, actors, item["id"], "FINANCE", "finance").json()
    assert result["status"] == "APPROVED"
    assert result["approvals"][1]["approver"]["id"] == actors["FINANCE"].id
    assert client.get("/approvals/pending", headers=headers(actors["FINANCE"])).json()["items"] == []
    assert client.get(f'/requests/{item["id"]}', headers=headers(actors["FINANCE"])).status_code == 200
    low = submit(client, actors).json()
    decide(client, actors, low["id"])
    assert decide(client, actors, low["id"], "FINANCE", "finance").status_code == 404


def test_cancellation_closes_pending_approval(client, actors):
    item = submit(client, actors).json()
    url = f'/requests/{item["id"]}/cancel'
    assert client.patch(url, headers=headers(actors["OTHER"])).status_code == 404
    assert client.patch(url, headers=headers(actors["MANAGER"])).status_code == 403
    result = client.patch(url, headers=headers(actors["EMPLOYEE"]))
    assert result.status_code == 200
    assert result.json()["status"] == "CANCELLED"
    assert result.json()["approvals"][0]["status"] == "CANCELLED"
    assert decide(client, actors, item["id"]).status_code == 409
    assert client.patch(url, headers=headers(actors["EMPLOYEE"])).status_code == 409
    assert client.get("/approvals/pending", headers=headers(actors["MANAGER"])).json()["items"] == []


@pytest.mark.parametrize("status", [RequestStatus.REJECTED, RequestStatus.CANCELLED, RequestStatus.COMPLETED, RequestStatus.PROCESSING, RequestStatus.DRAFT, RequestStatus.APPROVED])
def test_terminal_and_unimplemented_states_have_no_transition(status):
    for action in Action:
        if (status, action) in ((RequestStatus.APPROVED, Action.START_PROCESSING), (RequestStatus.PROCESSING, Action.COMPLETE)):
            continue  # Explicitly implemented by Phase 5, tested by fulfillment tests.
        with pytest.raises(HTTPException) as error:
            next_status(status, action, Decimal("10000000"))
        assert error.value.status_code == 409


def test_duplicate_approval_constraint(client, actors, db):
    item = submit(client, actors).json()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(Approval(request_id=item["id"], approver_id=actors["MANAGER"].id,
                            approval_type=ApprovalType.MANAGER, status=ApprovalStatus.PENDING))
            db.flush()


def test_workflow_transaction_rolls_back_on_finance_insert_failure(client, actors, db, monkeypatch):
    item = submit(client, actors, estimated_cost="10000000").json()
    original_flush = db.flush
    def fail_finance(*args, **kwargs):
        if any(isinstance(obj, Approval) and obj.approval_type == ApprovalType.FINANCE for obj in db.new):
            raise RuntimeError("Simulated write failure")
        return original_flush(*args, **kwargs)
    with pytest.raises(RuntimeError):
        with db.begin_nested():
            monkeypatch.setattr(db, "flush", fail_finance)
            workflow.transition(db, item["id"], actors["MANAGER"], Action.MANAGER_APPROVE,
                                DecisionInput(decision=Decision.APPROVE))
    monkeypatch.setattr(db, "flush", original_flush)
    db.expire_all()
    request = db.get(Request, item["id"])
    assert request.status == RequestStatus.PENDING_MANAGER_APPROVAL
    assert len(request.approvals) == 1 and request.approvals[0].status == ApprovalStatus.PENDING
