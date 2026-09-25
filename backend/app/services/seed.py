import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DatabaseSettings
from app.core.security import hash_password
from app.database import create_database
from app.models import Role, User
from app.schemas.auth import SeedUserInput

# Public credentials for synthetic demo accounts only; never an application secret.
DEMO_PASSWORD = "RequestFlow-Demo!2026"
DEMO_USERS = (
    ("Morgan Manager", "manager@requestflow.demo", Role.MANAGER),
    ("Jamie Employee", "employee@requestflow.demo", Role.EMPLOYEE),
    ("Frankie Finance", "finance@requestflow.demo", Role.FINANCE),
    ("Parker Procurement", "procurement@requestflow.demo", Role.PROCUREMENT),
    ("Alex Admin", "admin@requestflow.demo", Role.ADMIN),
)


def seed_demo_users(db: Session) -> None:
    users: dict[Role, User] = {}
    for name, email, role in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            data = SeedUserInput(name=name, email=email, password=DEMO_PASSWORD, role=role)
            user = User(name=data.name, email=str(data.email), role=data.role,
                        hashed_password=hash_password(data.password.get_secret_value()), is_active=True)
            db.add(user)
            db.flush()
        elif user.role != role:
            raise ValueError(f"Existing demo account {email} has a different role; seed stopped")
        users[role] = user
    employee = users[Role.EMPLOYEE]
    manager = users[Role.MANAGER]
    if employee.manager_id is None:
        employee.manager_id = manager.id
    elif employee.manager_id != manager.id:
        raise ValueError("Demo employee already has a different manager; seed stopped")
    db.flush()


def main():
    parser = argparse.ArgumentParser(description="Create public demo accounts; never run against private production data")
    parser.add_argument("--demo", action="store_true", required=True, help="Confirm this is a demo database")
    parser.parse_args()
    engine, sessions = create_database(DatabaseSettings())
    try:
        with sessions.begin() as db:
            seed_demo_users(db)
        print("Demo users ready (5 accounts). Existing passwords and active status were preserved.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
