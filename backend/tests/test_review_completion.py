import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text

from app.database import SessionLocal
from app.models.clause_evaluation import ClauseEvaluation
from app.models.clause_type import ClauseType
from app.models.review import Review, ReviewStatus
from app.models.risk_label import RiskLabel
from app.workers import tasks

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    pytest.skip("DATABASE_URL not set", allow_module_level=True)


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


@pytest.fixture(autouse=True)
def _stub_processing(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.workers.tasks.get_storage_client",
        lambda: type("Stub", (), {"get_bytes": lambda _self, _key: b"data"})(),
    )
    monkeypatch.setattr(
        "app.workers.tasks.extract_document",
        lambda _content, _mime: {"raw_text": "", "pages": []},
    )
    segments = [
        {
            "segment_index": 0,
            "heading": "GOVERNING LAW",
            "section_number": None,
            "text": "This agreement is governed by law. governing law applies.",
            "hash": "hash1",
            "page_start": 1,
            "page_end": 1,
        }
    ]
    monkeypatch.setattr("app.workers.tasks.segment_document", lambda *_args: segments)

    monkeypatch.setattr(
        "app.workers.tasks.classify_segment",
        lambda _text: [
            {"clause_type": ClauseType.GOVERNING_LAW, "confidence": 0.9, "method": "RULES"}
        ],
    )

    monkeypatch.setattr(
        "app.workers.tasks.evaluate_clause",
        lambda *_args: {
            "risk_label": RiskLabel.YELLOW.value,
            "short_reason": "stub",
            "suggested_change": "stub",
            "candidate_quotes": ["governing law"],
            "triggered_rule_ids": ["R1"],
        },
    )



def test_process_review_marks_completed() -> None:
    review_id = uuid4()
    with SessionLocal() as session:
        session.add(
            Review(
                id=review_id,
                status=ReviewStatus.PROCESSING,
                doc_storage_key="reviews/key",
                doc_mime="application/pdf",
            )
        )
        session.commit()

    tasks.process_review(review_id)
    tasks.process_review(review_id)

    with SessionLocal() as session:
        review = session.get(Review, review_id)
        assert review.status == ReviewStatus.COMPLETED

        evaluations = session.execute(select(ClauseEvaluation)).scalars().all()
        assert len(evaluations) == len(ClauseType)

        tasks.process_review(review_id)
        evaluations_again = session.execute(select(ClauseEvaluation)).scalars().all()
        assert len(evaluations_again) == len(ClauseType)
