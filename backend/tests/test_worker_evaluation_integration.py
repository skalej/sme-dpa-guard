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
        },
        {
            "segment_index": 1,
            "heading": "SECURITY",
            "section_number": None,
            "text": "Security measures include encryption.",
            "hash": "hash2",
            "page_start": 2,
            "page_end": 2,
        },
    ]
    monkeypatch.setattr("app.workers.tasks.segment_document", lambda *_args: segments)

    def _classify(text: str):
        if "governing law" in text:
            return [{"clause_type": ClauseType.GOVERNING_LAW, "confidence": 0.9, "method": "RULES"}]
        return [{"clause_type": ClauseType.SECURITY_TOMS, "confidence": 0.8, "method": "RULES"}]

    monkeypatch.setattr("app.workers.tasks.classify_segment", _classify)

    def _eval_stub(_clause_type, segment_texts, _context, _rules):
        return {
            "risk_label": RiskLabel.YELLOW.value,
            "short_reason": "stub",
            "suggested_change": "stub",
            "candidate_quotes": ["governing law", "missing quote"],
            "triggered_rule_ids": ["R1"],
        }

    monkeypatch.setattr("app.workers.tasks.evaluate_clause", _eval_stub)



def test_process_review_evaluations_idempotent() -> None:
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
        evaluations = session.execute(select(ClauseEvaluation)).scalars().all()
        assert len(evaluations) == len(ClauseType)

        gov_eval = session.execute(
            select(ClauseEvaluation).where(
                ClauseEvaluation.review_id == review_id,
                ClauseEvaluation.clause_type == ClauseType.GOVERNING_LAW,
            )
        ).scalar_one()
        assert gov_eval.evidence_spans
        assert gov_eval.evidence_spans[0]["quote"] == "governing law"

        transfers = session.execute(
            select(ClauseEvaluation).where(
                ClauseEvaluation.review_id == review_id,
                ClauseEvaluation.clause_type == ClauseType.TRANSFERS,
            )
        ).scalar_one()
        assert transfers.risk_label == RiskLabel.RED

        liability = session.execute(
            select(ClauseEvaluation).where(
                ClauseEvaluation.review_id == review_id,
                ClauseEvaluation.clause_type == ClauseType.LIABILITY,
            )
        ).scalar_one()
        assert liability.risk_label == RiskLabel.YELLOW
