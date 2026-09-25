from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi import Depends
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, require_roles
from app.config import Settings
from app.main import create_app
from app.models import Role
from app.services.seed import seed_demo_users


def migration_config(connection):
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.attributes["connection"] = connection
    return config


@contextmanager
def isolated_schema():
    # No public tables are touched. Every run gets its own temporary PostgreSQL schema.
    engine = create_engine(Settings().sqlalchemy_url())
    schema = f"test_{uuid4().hex}"
    with engine.connect() as connection:
        connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
        connection.exec_driver_sql(f'SET search_path TO "{schema}"')
        connection.commit()
        try:
            yield connection
        finally:
            connection.rollback()
            connection.exec_driver_sql('SET search_path TO public')
            connection.exec_driver_sql(f'DROP SCHEMA "{schema}" CASCADE')
            connection.commit()
    engine.dispose()


@pytest.fixture(scope="session")
def connection():
    with isolated_schema() as connection:
        command.upgrade(migration_config(connection), "head")
        connection.commit()
        yield connection


@pytest.fixture
def db(connection):
    transaction = connection.begin()
    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        yield session
    transaction.rollback()


@pytest.fixture
def seeded(db):
    seed_demo_users(db)
    db.commit()
    return db


@pytest.fixture
def client(db):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    @app.get("/_test/manager", dependencies=[Depends(require_roles(Role.MANAGER, Role.ADMIN))])
    def manager_only():
        return {"allowed": True}

    with TestClient(app) as client:
        yield client
