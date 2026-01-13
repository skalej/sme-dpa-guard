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
def _stub_worker(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.reviews.process_review", lambda _id: None)



def test_start_requires_uploaded() -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    response = client.post(f"/reviews/{review_id}/start")

    assert response.status_code == 409



def test_start_transitions_to_processing() -> None:
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
    assert response.json()["status"] == ReviewStatus.PROCESSING.value

    get_response = client.get(f"/reviews/{review_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == ReviewStatus.PROCESSING.value



def test_start_unknown_review_404() -> None:
    response = client.post("/reviews/00000000-0000-0000-0000-000000000000/start")

    assert response.status_code == 404
