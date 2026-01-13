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
        connection.execute(text("TRUNCATE TABLE reviews"))


@pytest.fixture(autouse=True)
def _fake_storage(monkeypatch) -> FakeStorageClient:
    fake_client = FakeStorageClient()
    monkeypatch.setattr(
        "app.services.uploads.get_storage_client", lambda: fake_client
    )
    return fake_client



def test_upload_transitions_to_uploaded(_fake_storage: FakeStorageClient) -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    files = {
        "file": ("contract.pdf", b"%PDF-1.4 test", "application/pdf")
    }
    response = client.post(f"/reviews/{review_id}/upload", files=files)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == ReviewStatus.UPLOADED.value
    assert payload["doc"]["filename"] == "contract.pdf"
    assert payload["doc"]["storage_key"].startswith(f"reviews/{review_id}/source/")
    assert _fake_storage.uploads

    get_response = client.get(f"/reviews/{review_id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == ReviewStatus.UPLOADED.value
    assert get_response.json()["doc"]["storage_key"]



def test_upload_wrong_status_rejected() -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE reviews SET status = :status WHERE id = :id"),
            {"status": ReviewStatus.UPLOADED.value, "id": review_id},
        )

    files = {"file": ("contract.pdf", b"%PDF-1.4 test", "application/pdf")}
    response = client.post(f"/reviews/{review_id}/upload", files=files)

    assert response.status_code == 409



def test_upload_unsupported_type() -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    files = {"file": ("contract.txt", b"hello", "text/plain")}
    response = client.post(f"/reviews/{review_id}/upload", files=files)

    assert response.status_code == 415
