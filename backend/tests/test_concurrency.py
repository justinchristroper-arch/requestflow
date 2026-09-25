from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from alembic import command
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import ApprovalStatus, AuditAction, AuditLog, Request, RequestStatus, Role, User
from app.schemas.request import DecisionInput, RequestInput
from app.services.requests import create_request
from app.services.seed import seed_demo_users
from app.services.workflow import Action, transition
from conftest import isolated_schema, migration_config


def test_concurrent_creation_and_competing_approval_decisions():
    with isolated_schema() as connection:
        command.upgrade(migration_config(connection), "head")
        connection.commit()
        schema = connection.exec_driver_sql("SELECT current_schema()").scalar_one()
        connection.commit()
        engine = create_engine(connection.engine.url, connect_args={"options": f"-csearch_path={schema}"})
        try:
            with Session(engine) as db, db.begin():
                seed_demo_users(db)
                employee_id = db.scalar(select(User.id).where(User.role == Role.EMPLOYEE))
                manager_id = db.scalar(select(User.id).where(User.role == Role.MANAGER))
                finance_id = db.scalar(select(User.id).where(User.role == Role.FINANCE))
                procurement_id = db.scalar(select(User.id).where(User.role == Role.PROCUREMENT))
                second_operator = User(name="Second operator", email="second@requestflow.demo", role=Role.PROCUREMENT,
                                       hashed_password="unused-in-service-tests")
                db.add(second_operator)
                db.flush()
                second_operator_id = second_operator.id
            start = Barrier(4)
            def create_one(_):
                with Session(engine) as db, db.begin():
                    employee = db.get(User, employee_id)
                    start.wait(timeout=10)
                    request = create_request(db, employee, RequestInput(category="HARDWARE", title="Concurrent demo",
                        description="Concurrency test", business_justification="Verify integrity", estimated_cost="10000000", priority="HIGH"))
                    return request.id, request.request_number
            with ThreadPoolExecutor(max_workers=4) as pool:
                created = list(pool.map(create_one, range(4)))
            assert len({number for _, number in created}) == 4
            request_id = created[0][0]

            def compete(actor_id, action):
                barrier = Barrier(2)
                def decide(_):
                    try:
                        with Session(engine) as db, db.begin():
                            actor = db.get(User, actor_id)
                            barrier.wait(timeout=10)
                            result = transition(db, request_id, actor, action, DecisionInput(decision="APPROVE"))
                            return result.status.value
                    except HTTPException as error:
                        return error.status_code
                with ThreadPoolExecutor(max_workers=2) as pool:
                    return list(pool.map(decide, range(2)))

            assert sorted(map(str, compete(manager_id, Action.MANAGER_APPROVE))) == ["409", "PENDING_FINANCE_APPROVAL"]
            assert sorted(map(str, compete(finance_id, Action.FINANCE_APPROVE))) == ["409", "APPROVED"]
            with Session(engine) as db:
                result = db.get(Request, request_id)
                assert result.status == RequestStatus.APPROVED
                assert len(result.approvals) == 2
                assert all(approval.status == ApprovalStatus.APPROVED for approval in result.approvals)
            assert sorted(map(str, compete(procurement_id, Action.START_PROCESSING))) == ["409", "PROCESSING"]
            assert sorted(map(str, compete(procurement_id, Action.COMPLETE))) == ["409", "COMPLETED"]
            with Session(engine) as db:
                result = db.get(Request, request_id)
                assert result.status == RequestStatus.COMPLETED
                assert result.processing_owner_id == procurement_id
                actions = db.scalars(select(AuditLog.action).where(AuditLog.request_id == request_id)).all()
                assert actions.count(AuditAction.PROCESSING_STARTED) == 1
                assert actions.count(AuditAction.REQUEST_COMPLETED) == 1

            # Conflicting decisions must have exactly one winner, regardless of scheduling.
            request_id = created[1][0]
            barrier = Barrier(2)
            def opposing_decision(action):
                try:
                    with Session(engine) as db, db.begin():
                        actor = db.get(User, manager_id)
                        barrier.wait(timeout=10)
                        decision = DecisionInput(decision="REJECT", comment="Conflicting test decision") if action == Action.MANAGER_REJECT else DecisionInput(decision="APPROVE")
                        return transition(db, request_id, actor, action, decision).status.value
                except HTTPException as error:
                    return error.status_code
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(opposing_decision, (Action.MANAGER_APPROVE, Action.MANAGER_REJECT)))
            assert results.count(409) == 1
            with Session(engine) as db:
                request = db.get(Request, request_id)
                actions = db.scalars(select(AuditLog.action).where(AuditLog.request_id == request_id)).all()
                assert sum(action in (AuditAction.MANAGER_APPROVED, AuditAction.MANAGER_REJECTED) for action in actions) == 1
                assert len(request.approvals) == (2 if request.status == RequestStatus.PENDING_FINANCE_APPROVAL else 1)

            # Different operators compete for ownership of the same approved request.
            request_id = created[2][0]
            with Session(engine) as db, db.begin():
                transition(db, request_id, db.get(User, manager_id), Action.MANAGER_APPROVE, DecisionInput(decision="APPROVE"))
                transition(db, request_id, db.get(User, finance_id), Action.FINANCE_APPROVE, DecisionInput(decision="APPROVE"))
            barrier = Barrier(2)
            def claim(operator_id):
                try:
                    with Session(engine) as db, db.begin():
                        actor = db.get(User, operator_id)
                        barrier.wait(timeout=10)
                        transition(db, request_id, actor, Action.START_PROCESSING)
                        return operator_id
                except HTTPException as error:
                    assert error.status_code == 409
                    return None
            with ThreadPoolExecutor(max_workers=2) as pool:
                claims = list(pool.map(claim, (procurement_id, second_operator_id)))
            assert claims.count(None) == 1
            winner = next(value for value in claims if value is not None)
            with Session(engine) as db:
                assert db.get(Request, request_id).processing_owner_id == winner
                events = db.scalars(select(AuditLog).where(AuditLog.request_id == request_id, AuditLog.action == AuditAction.PROCESSING_STARTED)).all()
                assert len(events) == 1 and events[0].actor_id == winner
        finally:
            engine.dispose()
