from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import func, select

from app.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Role, User
from app.services.seed import DEMO_PASSWORD, seed_demo_users


def login(client, email="employee@requestflow.demo", password=DEMO_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_password_hashing():
    first = hash_password(DEMO_PASSWORD)
    second = hash_password(DEMO_PASSWORD)
    assert first.startswith("$argon2id$")
    assert first != second and DEMO_PASSWORD not in first
    assert verify_password(DEMO_PASSWORD, first)
    assert not verify_password("incorrect", first)


def test_login_and_current_profile(client, seeded):
    response = login(client, email="  EMPLOYEE@requestflow.demo  ")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == Settings().access_token_expire_minutes * 60
    assert body["user"]["role"] == "EMPLOYEE"
    assert body["user"]["manager"]["email"] == "manager@requestflow.demo"
    assert "password" not in response.text
    me = client.get("/auth/me", headers=auth_header(body["access_token"]))
    assert me.status_code == 200
    assert me.json() == body["user"]
    assert me.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("email,password", [
    ("employee@requestflow.demo", "incorrect"), ("unknown@requestflow.demo", DEMO_PASSWORD),
])
def test_bad_credentials_are_indistinguishable(client, seeded, email, password):
    response = login(client, email, password)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


@pytest.mark.parametrize("headers", [{}, auth_header("garbage"), {"Authorization": "Basic abc"}])
def test_me_rejects_missing_or_invalid_token(client, headers):
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_tampered_wrong_algorithm_and_incomplete_tokens(client, seeded):
    settings = Settings()
    employee = seeded.scalar(select(User).where(User.role == Role.EMPLOYEE))
    now = datetime.now(timezone.utc)
    claims = {"sub": str(employee.id), "iat": now - timedelta(hours=2),
              "exp": now - timedelta(hours=1), "iss": "requestflow-api", "aud": "requestflow-web"}
    secret = settings.jwt_secret.get_secret_value()
    tokens = [jwt.encode(claims, secret, algorithm="HS256")]
    claims["exp"] = now + timedelta(hours=1)
    tokens += [jwt.encode(claims, "wrong-signing-key-with-at-least-32-bytes", algorithm="HS256"),
               jwt.encode(claims, secret, algorithm="HS384"),
               jwt.encode({"sub": str(employee.id)}, secret, algorithm="HS256")]
    for token in tokens:
        assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


def test_inactive_user_and_deleted_identity(client, seeded):
    token = login(client).json()["access_token"]
    employee = seeded.scalar(select(User).where(User.role == Role.EMPLOYEE))
    employee.is_active = False
    seeded.commit()
    assert login(client).status_code == 401
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401
    seeded.delete(employee)
    seeded.commit()
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


def test_seed_idempotence_and_manager_link(db):
    seed_demo_users(db)
    db.commit()
    users = db.scalars(select(User)).all()
    original = {user.email: (user.id, user.hashed_password) for user in users}
    admin = next(user for user in users if user.role == Role.ADMIN)
    admin.is_active = False
    admin.hashed_password = hash_password("Changed-demo-password")
    db.commit()
    seed_demo_users(db)
    db.commit()
    assert db.scalar(select(func.count()).select_from(User)) == 5
    employee = db.scalar(select(User).where(User.role == Role.EMPLOYEE))
    assert employee.manager.role == Role.MANAGER
    assert employee.manager.email == "manager@requestflow.demo"
    assert employee.hashed_password == original[employee.email][1]
    assert not admin.is_active and verify_password("Changed-demo-password", admin.hashed_password)


def test_role_helper_uses_current_database_role(client, seeded):
    employee_token = login(client).json()["access_token"]
    assert client.get("/_test/manager", headers=auth_header(employee_token)).status_code == 403
    for email in ("manager@requestflow.demo", "admin@requestflow.demo"):
        token = login(client, email).json()["access_token"]
        assert client.get("/_test/manager", headers=auth_header(token)).status_code == 200
    employee = seeded.scalar(select(User).where(User.role == Role.EMPLOYEE))
    employee.role = Role.MANAGER
    seeded.commit()
    assert client.get("/_test/manager", headers=auth_header(employee_token)).status_code == 200


def test_client_cannot_supply_role(client, seeded):
    response = client.post("/auth/login", json={"email": "employee@requestflow.demo",
                           "password": DEMO_PASSWORD, "role": "ADMIN"})
    assert response.status_code == 422


def test_auth_cors_preflight(client):
    response = client.options("/auth/me", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization",
    })
    assert response.status_code == 200
    assert "Authorization" in response.headers["access-control-allow-headers"]


def test_invalid_subject_rejected(client):
    settings = Settings()
    token = create_access_token(2147483648, settings)
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401
