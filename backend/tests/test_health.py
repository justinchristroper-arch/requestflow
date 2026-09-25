from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.main import create_app


def test_liveness_does_not_require_database():
    app = create_app(Settings(postgres_password="test"))
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {
            "status": "ok", "service": "requestflow-api"
        }


def test_readiness_failure_is_safe():
    app = create_app(Settings(postgres_password="test"))
    app.state.engine = MagicMock()
    app.state.engine.connect.side_effect = OperationalError("private", {}, Exception("secret"))
    with TestClient(app) as client:
        response = client.get("/api/health/ready")
        assert response.status_code == 503
        assert response.json() == {"detail": "Database unavailable"}


def test_cors_allows_frontend_only():
    app = create_app(Settings(postgres_password="test"))
    with TestClient(app) as client:
        allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
        denied = client.get("/api/health", headers={"Origin": "https://unrelated.example"})
        assert "access-control-allow-origin" not in denied.headers
