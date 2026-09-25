"""Explicit, additive demo data. All history is created through workflow services."""
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.config import DatabaseSettings
from app.database import create_database
from app.models import Category, Priority, Request, Role, User
from app.schemas.request import DecisionInput, RequestInput
from app.services.requests import create_request
from app.services.rules import PRIORITY_DAYS
from app.services.seed import seed_demo_users
from app.services.workflow import Action, transition

MARKER = "Synthetic analytics demo v1; not measured business performance."
TITLES = ["Service desk monitor", "Design software renewal", "Reporting access", "Laptop battery repair", "Meeting room equipment"]


def seed_analytics(db, *, as_of: datetime):
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must include a timezone")
    # Serialize parallel seed runs; unique request numbers remain sequence-owned.
    db.execute(text("SELECT pg_advisory_xact_lock(78082026)"))
    seed_demo_users(db)
    users = {role: db.scalar(select(User).where(User.email == f"{role.value.lower()}@requestflow.demo")) for role in Role}
    if any(not user.is_active for user in users.values()):
        raise ValueError("Demo accounts must be active; existing account settings were preserved")
    anchor = as_of.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    added = 0
    for i in range(30):
        title = f"[DEMO Analytics v1 {i + 1:02d}] {TITLES[i % 5]}"
        existing = db.scalars(select(Request).where(Request.title == title)).all()
        if existing:
            if len(existing) != 1 or existing[0].description != MARKER:
                raise ValueError("Demo title collision; existing data was not overwritten")
            continue
        priority = [Priority.HIGH, Priority.MEDIUM, Priority.LOW][i % 3]
        if i < 12:
            due = anchor + timedelta(hours=[-12, 12, 48][i % 3])
            created = due - timedelta(days=PRIORITY_DAYS[priority])
        else:
            month_index = anchor.year * 12 + anchor.month - 1 - (i % 6)
            created = datetime(month_index // 12, month_index % 12 + 1, 2 + i % 7, tzinfo=timezone.utc)
            # Keep generated completed events in the past, including early-month runs.
            created = min(created, anchor - timedelta(days=8))
        high = i % 2 == 1 or i in (4, 5)
        request = create_request(db, users[Role.EMPLOYEE], RequestInput(category=list(Category)[i % 5],
            title=title, description=MARKER, business_justification="Synthetic service request for a portfolio demonstration.",
            estimated_cost="10000000" if high else "2000000", priority=priority), now=created)
        def act(role, action, hours, decision=None, note=None):
            return transition(db, request.id, users[role], action, decision, note=note, now=created + timedelta(hours=hours))
        if i < 4:
            pass  # Pending Manager
        elif i >= 27:
            act(Role.EMPLOYEE, Action.CANCEL, 1)
        elif i >= 24:
            act(Role.MANAGER, Action.MANAGER_REJECT, 1, DecisionInput(decision="REJECT", comment="Demo: outside the approved budget."))
        else:
            act(Role.MANAGER, Action.MANAGER_APPROVE, 1, DecisionInput(decision="APPROVE", comment="Demo: business need reviewed."))
            if i not in (4, 5):
                if high:
                    act(Role.FINANCE, Action.FINANCE_APPROVE, 2, DecisionInput(decision="APPROVE"))
                if i >= 9:
                    act(Role.PROCUREMENT, Action.START_PROCESSING, 3, note="Demo: fulfillment started.")
                    if i >= 12:
                        act(Role.PROCUREMENT, Action.COMPLETE, PRIORITY_DAYS[priority] * 24 + (-6 if i % 2 == 0 else 6), note="Demo: fulfillment verified.")
        added += 1
    db.flush()
    return added


def main():
    parser = argparse.ArgumentParser(description="Add 30 synthetic analytics requests without replacing existing data")
    parser.add_argument("--demo", action="store_true", required=True)
    parser.add_argument("--as-of", type=datetime.fromisoformat, help="Timezone-aware ISO reference timestamp; defaults to current UTC")
    args = parser.parse_args()
    engine, sessions = create_database(DatabaseSettings())
    try:
        with sessions.begin() as db:
            added = seed_analytics(db, as_of=args.as_of or datetime.now(timezone.utc))
        print(f"Analytics demo ready: {added} requests added; existing requests preserved.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
