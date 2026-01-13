import os
from pathlib import Path
import json

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app
from app.models.clause_type import ClauseType
from app.models.risk_label import RiskLabel

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
def _clean_db() -> None:
    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE clause_evaluations, segment_classifications, review_segments, reviews"
            )
        )



def test_explain_empty_then_populated() -> None:
    create_response = client.post("/reviews")
    review_id = create_response.json()["review_id"]

    response = client.get(f"/reviews/{review_id}/explain")

    assert response.status_code == 200
    payload = response.json()
    assert payload["review_id"] == review_id
    assert payload["evaluations"] == []

    engine = create_engine(DATABASE_URL, future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO clause_evaluations (review_id, clause_type, risk_label, short_reason, suggested_change, triggered_rule_ids, evidence_spans) "
                "VALUES (:review_id, :clause_type, :risk_label, :short_reason, :suggested_change, :triggered_rule_ids, :evidence_spans)"
            ),
            {
                "review_id": review_id,
                "clause_type": ClauseType.GOVERNING_LAW.value,
                "risk_label": RiskLabel.YELLOW.value,
                "short_reason": "stub",
                "suggested_change": "stub",
                "triggered_rule_ids": json.dumps(["R1"]),
                "evidence_spans": json.dumps([]),
            },
        )

    response = client.get(f"/reviews/{review_id}/explain")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["evaluations"]) == 1
    assert payload["evaluations"][0]["clause_type"] == ClauseType.GOVERNING_LAW.value
    assert isinstance(payload["evaluations"][0]["evidence_spans"], list)
