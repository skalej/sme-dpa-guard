import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app
from app.models.review import ReviewStatus
from app.storage.base import StorageClient

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    pytest.skip("DATABASE_URL not set", allow_module_level=True)

client = TestClient(app)


class FakeStorageClient(StorageClient):
    def __init__(self) -> None:
        self.uploads: list[tuple[str, bytes, str]] = []

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        self.uploads.append((key, data, content_type))


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
def _fake_storage(monkeypatch) -> FakeStorageClient:
    fake_client = FakeStorageClient()
    monkeypatch.setattr(
        "app.services.uploads.get_storage_client", lambda: fake_client
    )
    return fake_client


@pytest.fixture(autouse=True)
def _stub_worker(monkeypatch) -> None:
    class _Result:
        id = "job-1"
        status = "PENDING"

    monkeypatch.setattr(
        "app.api.routes.reviews.process_review_task",
        type("Stub", (), {"delay": lambda *_args, **_kwargs: _Result()}),
    )


def test_submit_success_with_fields(_fake_storage: FakeStorageClient) -> None:
    files = {"file": ("contract.pdf", b"%PDF-1.4 test", "application/pdf")}
    data = {"company_role": "controller", "region": "EU", "vendor_type": "SaaS"}
    response = client.post("/reviews/submit", files=files, data=data)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "processing"
    assert payload["job_id"] == "job-1"
    assert _fake_storage.uploads

    engine = create_engine(DATABASE_URL, future=True)
    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT status, job_id FROM reviews WHERE id = :id"),
            {"id": payload["review_id"]},
        ).one()
    assert row.status == ReviewStatus.PROCESSING.value
    assert row.job_id == "job-1"


def test_submit_invalid_context_json() -> None:
    files = {"file": ("contract.pdf", b"%PDF-1.4 test", "application/pdf")}
    data = {"context_json": "{bad json"}
    response = client.post("/reviews/submit", files=files, data=data)

    assert response.status_code == 400


def test_submit_missing_file() -> None:
    data = {"company_role": "controller", "region": "EU"}
    response = client.post("/reviews/submit", data=data)

    assert response.status_code == 400


def test_submit_unsupported_file_type() -> None:
    files = {"file": ("contract.txt", b"hello", "text/plain")}
    data = {"company_role": "controller", "region": "EU"}
    response = client.post("/reviews/submit", files=files, data=data)

    assert response.status_code == 415
