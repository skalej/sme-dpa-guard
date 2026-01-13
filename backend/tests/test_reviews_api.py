import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    pytest.skip("DATABASE_URL not set", allow_module_level=True)

client = TestClient(app)


def _alembic_config() -> Config:
    base_dir = Path(__file__).resolve().parents[1]
    config = Config(str(base_dir / "alembic.ini"))
    config.set_main_option("script_location", str(base_dir / "alembic"))
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    return config


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    command.upgrade(_alembic_config(), "head")


@pytest.fixture(autouse=True)
def _clean_reviews() -> None:
    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE review_segments, reviews"))



def test_create_review_returns_created() -> None:
    response = client.post("/reviews", json={"context_json": {"foo": "bar"}})

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "CREATED"
    assert payload["context_json"] == {"foo": "bar"}
    assert "review_id" in payload



def test_get_review_returns_same() -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    response = client.get(f"/reviews/{review_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_id"] == review_id
    assert payload["status"] == "CREATED"



def test_get_unknown_returns_404() -> None:
    response = client.get("/reviews/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
