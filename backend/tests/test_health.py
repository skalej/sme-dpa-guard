from fastapi.testclient import TestClient

from app.api.routes import health
from app.main import app

client = TestClient(app)


def test_live_ok() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_db_down(monkeypatch) -> None:
    monkeypatch.setattr(health, "db_ping", lambda: False)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
