import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app
from app.models.review import ReviewStatus

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    pytest.skip("DATABASE_URL not set", allow_module_level=True)

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    config = Config(str(base_dir / "alembic.ini"))
    config.set_main_option("script_location", str(base_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def _clean_reviews() -> None:
    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE clause_evaluations, segment_classifications, review_segments, reviews"
            )
        )


@pytest.fixture(autouse=True)
def _stub_celery(monkeypatch) -> None:
    class _DelayResult:
        id = "job123"
        status = "PENDING"

    class _AsyncResult:
        state = "SUCCESS"

        def ready(self) -> bool:
            return True

        def successful(self) -> bool:
            return True

    monkeypatch.setattr(
        "app.api.routes.reviews.process_review_task",
        type("Stub", (), {"delay": lambda *_args, **_kwargs: _DelayResult()}),
    )
    monkeypatch.setattr(
        "app.api.routes.reviews.AsyncResult",
        lambda *_args, **_kwargs: _AsyncResult(),
    )


def test_start_persists_job_id() -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE reviews SET status = :status WHERE id = :id"),
            {"status": ReviewStatus.UPLOADED.value, "id": review_id},
        )

    response = client.post(f"/reviews/{review_id}/start")

    assert response.status_code == 200
    assert response.json()["job_id"] == "job123"

    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT job_id, job_status FROM reviews WHERE id = :id"),
            {"id": review_id},
        ).one()
    assert row.job_id == "job123"
    assert row.job_status == "PENDING"


def test_job_status_endpoint() -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE reviews SET status = :status WHERE id = :id"),
            {"status": ReviewStatus.UPLOADED.value, "id": review_id},
        )

    client.post(f"/reviews/{review_id}/start")
    job_response = client.get(f"/reviews/{review_id}/job")

    assert job_response.status_code == 200
    payload = job_response.json()
    assert payload["job_id"] == "job123"
    assert payload["state"] == "SUCCESS"
    assert payload["ready"] is True
    assert payload["successful"] is True
