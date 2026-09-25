from datetime import datetime, timedelta, timezone

from alembic import command
import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.models import AuditAction, AuditLog, Request, RequestStatus, Role, User
from app.schemas.request import DecisionInput, RequestInput
from app.services import audit, requests, workflow
from conftest import isolated_schema, migration_config
from test_requests import actors, headers, submit, decide, PAYLOAD  # fixtures/helpers from the existing request suite


def events(client, actors, request_id, role="EMPLOYEE"):
    return client.get(f"/requests/{request_id}/audit", headers=headers(actors[role]))


def fulfill(client, actors, request_id, action="start-processing", role="PROCUREMENT", note=None):
    return client.post(f"/requests/{request_id}/{action}", headers=headers(actors[role]), json={"note": note})


def approved(client, actors, cost="2000000", **overrides):
    item = submit(client, actors, estimated_cost=cost, **overrides).json()
    decide(client, actors, item["id"])
    if item["finance_required"]:
        decide(client, actors, item["id"], "FINANCE", "finance")
    return item


@pytest.mark.parametrize("cost,expected", [
    ("2000000", ["REQUEST_CREATED", "MANAGER_APPROVED", "PROCESSING_STARTED", "REQUEST_COMPLETED"]),
    ("10000000", ["REQUEST_CREATED", "MANAGER_APPROVED", "FINANCE_APPROVAL_REQUIRED", "FINANCE_APPROVED", "PROCESSING_STARTED", "REQUEST_COMPLETED"]),
])
def test_full_lifecycle_and_audit(client, actors, cost, expected):
    item = approved(client, actors, cost)
    started = fulfill(client, actors, item["id"], note="Work scheduled.")
    assert started.status_code == 200
    body = started.json()
    assert body["status"] == "PROCESSING"
    assert body["processing_owner"]["id"] == actors["PROCUREMENT"].id
    assert body["processing_started_at"] and body["completed_at"] is None
    assert body["allowed_actions"] == ["complete"]
    completed = fulfill(client, actors, item["id"], "complete", note="Equipment delivered.")
    assert completed.status_code == 200
    final = completed.json()
    assert final["status"] == "COMPLETED" and final["allowed_actions"] == []
    assert datetime.fromisoformat(final["completed_at"]) >= datetime.fromisoformat(final["processing_started_at"])
    history = events(client, actors, item["id"]).json()
    assert [event["action"] for event in history] == expected
    assert [(event["created_at"], event["id"]) for event in history] == sorted((event["created_at"], event["id"]) for event in history)
    assert history[0]["actor"]["id"] == actors["EMPLOYEE"].id
    assert history[0]["previous_status"] is None
    assert history[1]["actor"]["id"] == actors["MANAGER"].id
    assert history[-2]["previous_status"] == "APPROVED" and history[-2]["new_status"] == "PROCESSING"
    assert history[-1]["previous_status"] == "PROCESSING" and history[-1]["new_status"] == "COMPLETED"
    assert history[-2]["details"] == "Work scheduled."
    assert history[-1]["details"] == "Equipment delivered."
    assert history[-1]["actor"]["id"] == actors["PROCUREMENT"].id
    if item["finance_required"]:
        assert history[2]["actor"] is None and history[2]["previous_status"] is None
        assert "5,000,000.00" in history[2]["details"]
        assert history[3]["actor"]["id"] == actors["FINANCE"].id
    assert client.get("/procurement/queue", headers=headers(actors["PROCUREMENT"])).json()["total"] == 0
    assert events(client, actors, item["id"], "PROCUREMENT").status_code == 200
    assert "hashed_password" not in events(client, actors, item["id"]).text


@pytest.mark.parametrize("role", ["EMPLOYEE", "MANAGER", "FINANCE", "ADMIN"])
def test_other_roles_cannot_fulfill_or_access_queue(client, actors, role):
    item = approved(client, actors, "10000000")
    assert fulfill(client, actors, item["id"], role=role).status_code == 403
    fulfill(client, actors, item["id"])
    assert fulfill(client, actors, item["id"], "complete", role=role).status_code == 403
    assert client.get("/procurement/queue", headers=headers(actors[role])).status_code == 403


def test_only_processing_owner_can_complete(client, actors, db):
    other = User(name="Second operator", email="second.procurement@requestflow.demo", role=Role.PROCUREMENT,
                 hashed_password=hash_password("Second-operator-password"))
    db.add(other)
    db.commit()
    actors["OTHER_OPERATOR"] = other
    item = approved(client, actors)
    fulfill(client, actors, item["id"])
    assert fulfill(client, actors, item["id"], "complete", "OTHER_OPERATOR").status_code == 403
    detail = client.get(f'/requests/{item["id"]}', headers=headers(other)).json()
    assert detail["allowed_actions"] == []
    assert fulfill(client, actors, item["id"], "complete").status_code == 200
    assert fulfill(client, actors, item["id"]).status_code == 409
    assert fulfill(client, actors, item["id"], "complete").status_code == 409


def test_invalid_fulfillment_states_do_not_log_attempts(client, actors):
    item = submit(client, actors, estimated_cost="10000000").json()
    assert fulfill(client, actors, item["id"]).status_code == 404
    decide(client, actors, item["id"])
    assert fulfill(client, actors, item["id"]).status_code == 404
    decide(client, actors, item["id"], "FINANCE", "finance")
    before = events(client, actors, item["id"]).json()
    assert fulfill(client, actors, item["id"], "complete").status_code == 409
    assert events(client, actors, item["id"]).json() == before
    fulfill(client, actors, item["id"])
    assert fulfill(client, actors, item["id"]).status_code == 409


@pytest.mark.parametrize("outcome,expected", [("manager", "MANAGER_REJECTED"), ("finance", "FINANCE_REJECTED"), ("cancel", "REQUEST_CANCELLED")])
def test_rejection_cancellation_history_and_no_procurement_visibility(client, actors, outcome, expected):
    item = submit(client, actors, estimated_cost="10000000").json()
    if outcome == "cancel":
        client.patch(f'/requests/{item["id"]}/cancel', headers=headers(actors["EMPLOYEE"]))
    else:
        if outcome == "finance":
            decide(client, actors, item["id"])
        decide(client, actors, item["id"], outcome.upper(), outcome, "REJECT", "Outside budget.")
    history = events(client, actors, item["id"]).json()
    assert history[-1]["action"] == expected
    if outcome != "cancel":
        assert history[-1]["details"] == "Outside budget."
    assert fulfill(client, actors, item["id"]).status_code == 404
    assert events(client, actors, item["id"], "PROCUREMENT").status_code == 404
    assert client.get("/procurement/queue", headers=headers(actors["PROCUREMENT"])).json()["total"] == 0


def test_audit_visibility_matches_request_visibility(client, actors):
    item = submit(client, actors, estimated_cost="10000000").json()
    for role in ("EMPLOYEE", "MANAGER", "ADMIN"):
        assert events(client, actors, item["id"], role).status_code == 200
    for role in ("OTHER", "OTHER_MANAGER", "FINANCE", "PROCUREMENT"):
        assert events(client, actors, item["id"], role).status_code == 404
    assert client.get(f'/requests/{item["id"]}/audit').status_code == 401
    decide(client, actors, item["id"])
    assert events(client, actors, item["id"], "FINANCE").status_code == 200
    decide(client, actors, item["id"], "FINANCE", "finance")
    assert events(client, actors, item["id"], "PROCUREMENT").status_code == 200


def test_procurement_queue_filters_and_deterministic_order(client, actors, db):
    low = approved(client, actors, priority="LOW")
    high1 = approved(client, actors, priority="HIGH")
    high2 = approved(client, actors, priority="HIGH")
    medium = approved(client, actors, priority="MEDIUM")
    # Tie date fields explicitly: id is the final stable tie-breaker.
    moment = datetime.now(timezone.utc)
    for item in (high1, high2):
        request = db.get(Request, item["id"])
        request.created_at = moment
        request.due_date = moment + timedelta(days=1)
    db.commit()
    fulfill(client, actors, medium["id"])
    response = client.get("/procurement/queue", headers=headers(actors["PROCUREMENT"])).json()
    assert [item["id"] for item in response["items"]] == [high1["id"], high2["id"], medium["id"], low["id"]]
    in_progress = client.get("/procurement/queue?status=PROCESSING", headers=headers(actors["PROCUREMENT"])).json()
    assert [item["id"] for item in in_progress["items"]] == [medium["id"]]
    page = client.get("/procurement/queue?limit=1&offset=1", headers=headers(actors["PROCUREMENT"])).json()
    assert page["total"] == 4 and page["items"][0]["id"] == high2["id"]
    assert client.get("/procurement/queue?status=REJECTED", headers=headers(actors["PROCUREMENT"])).status_code == 422


@pytest.mark.parametrize("payload", [{"note": "x" * 2001}, {"processing_owner_id": 999}, {"status": "COMPLETED"}])
def test_fulfillment_payload_validation(client, actors, payload):
    item = approved(client, actors)
    assert client.post(f'/requests/{item["id"]}/start-processing', headers=headers(actors["PROCUREMENT"]), json=payload).status_code == 422


@pytest.mark.parametrize("operation", ["UPDATE audit_logs SET details='tampered'", "DELETE FROM audit_logs", "TRUNCATE audit_logs"])
def test_audit_rows_are_append_only(client, actors, db, operation):
    item = submit(client, actors).json()
    with pytest.raises(IntegrityError, match="append-only"):
        with db.begin_nested():
            db.execute(text(operation))
    assert len(events(client, actors, item["id"]).json()) == 1


@pytest.mark.parametrize("action", [workflow.Action.START_PROCESSING, workflow.Action.COMPLETE])
def test_fulfillment_and_audit_rollback_together(client, actors, db, monkeypatch, action):
    item = approved(client, actors)
    if action == workflow.Action.COMPLETE:
        fulfill(client, actors, item["id"])
    before = events(client, actors, item["id"]).json()
    previous = db.get(Request, item["id"]).status
    original = audit.record_event
    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("Simulated post-audit failure")
    with pytest.raises(RuntimeError):
        with db.begin_nested():
            monkeypatch.setattr(audit, "record_event", fail_after_write)
            workflow.transition(db, item["id"], actors["PROCUREMENT"], action, note="Must roll back")
    monkeypatch.setattr(audit, "record_event", original)
    db.expire_all()
    current = db.get(Request, item["id"])
    assert current.status == previous and current.completed_at is None
    if action == workflow.Action.START_PROCESSING:
        assert current.processing_owner_id is None and current.processing_started_at is None
    assert events(client, actors, item["id"]).json() == before


def test_manager_and_system_events_rollback_with_failed_routing(client, actors, db, monkeypatch):
    item = submit(client, actors, estimated_cost="10000000").json()
    original = audit.record_event
    def fail_system_event(*args, **kwargs):
        original(*args, **kwargs)
        if kwargs["action"] == AuditAction.FINANCE_APPROVAL_REQUIRED:
            raise RuntimeError("Simulated routing audit failure")
    with pytest.raises(RuntimeError):
        with db.begin_nested():
            monkeypatch.setattr(audit, "record_event", fail_system_event)
            workflow.transition(db, item["id"], actors["MANAGER"], workflow.Action.MANAGER_APPROVE, DecisionInput(decision="APPROVE"))
    monkeypatch.setattr(audit, "record_event", original)
    db.expire_all()
    request = db.get(Request, item["id"])
    assert request.status == RequestStatus.PENDING_MANAGER_APPROVAL and len(request.approvals) == 1
    assert [event["action"] for event in events(client, actors, item["id"]).json()] == ["REQUEST_CREATED"]


def test_request_creation_rolls_back_with_audit_failure(actors, db, monkeypatch):
    before = db.scalar(select(func.count()).select_from(Request))
    original = audit.record_event
    def fail_after_write(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("Simulated creation failure")
    with pytest.raises(RuntimeError):
        with db.begin_nested():
            monkeypatch.setattr(audit, "record_event", fail_after_write)
            requests.create_request(db, actors["EMPLOYEE"], RequestInput(**PAYLOAD))
    assert db.scalar(select(func.count()).select_from(Request)) == before
    assert db.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_upgrade_adds_factual_baseline_for_legacy_request():
    with isolated_schema() as connection:
        config = migration_config(connection)
        command.upgrade(config, "0002")
        user_id = connection.execute(text("INSERT INTO users (name,email,hashed_password,role) VALUES ('Legacy employee','legacy@requestflow.demo','unused','EMPLOYEE') RETURNING id")).scalar_one()
        connection.execute(text("INSERT INTO requests (request_number, requester_id,category,title,description,business_justification,estimated_cost,priority,status,due_date) VALUES ('LEGACY-1',:user_id,'OTHER','Legacy request','Existing data','Migration test',100,'LOW','APPROVED',now())"), {"user_id": user_id})
        command.upgrade(config, "head")
        row = connection.execute(text("SELECT action,actor_id,new_status,details FROM audit_logs")).one()
        assert row.action == "HISTORY_BASELINE" and row.actor_id is None and row.new_status == "APPROVED"
        assert "Earlier actions were not logged" in row.details
        command.check(config)
        command.downgrade(config, "0002")
        assert connection.scalar(text("SELECT count(*) FROM requests")) == 1
