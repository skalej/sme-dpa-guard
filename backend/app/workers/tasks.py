from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.errors import InvalidStatusTransition
from app.domain.status_flow import assert_transition
from app.models.clause_evaluation import ClauseEvaluation
from app.models.clause_type import ClauseType
from app.models.classification import SegmentClassification
from app.models.review import Review, ReviewStatus
from app.models.risk_label import RiskLabel
from app.models.segment import ReviewSegment
from app.playbook.rules import get_rules_for_clause_type
from app.services.evidence import validate_evidence_spans
from app.services.evaluation import evaluate_clause, evaluate_missing_clause
from app.services.extraction import extract_document
from app.services.classification import classify_segment
from app.services.segmentation import segment_document
from app.storage.minio import get_storage_client


def process_review(review_id: UUID) -> None:
    db: Session = SessionLocal()
    review: Review | None = None
    try:
        review = db.get(Review, review_id)
        if review is None:
            return
        if not review.doc_storage_key or not review.doc_mime:
            raise ValueError("Review has no document to process")

        storage = get_storage_client()
        content = storage.get_bytes(review.doc_storage_key)
        extraction_result = extract_document(content, review.doc_mime)
        segments = segment_document(
            extraction_result.get("raw_text", ""), extraction_result.get("pages")
        )
        if not segments:
            raise ValueError("No segments produced from document")

        db.execute(
            delete(SegmentClassification).where(
                SegmentClassification.review_id == review.id
            )
        )
        db.commit()

        db.execute(delete(ReviewSegment).where(ReviewSegment.review_id == review.id))
        db.add_all(
            [
                ReviewSegment(
                    review_id=review.id,
                    segment_index=segment["segment_index"],
                    heading=segment["heading"],
                    section_number=segment["section_number"],
                    text=segment["text"],
                    hash=segment["hash"],
                    page_start=segment["page_start"],
                    page_end=segment["page_end"],
                )
                for segment in segments
            ]
        )
        db.commit()

        segments = (
            db.execute(
                select(ReviewSegment)
                .where(ReviewSegment.review_id == review.id)
                .order_by(ReviewSegment.segment_index)
            )
            .scalars()
            .all()
        )

        classifications_to_add = []
        for segment in segments:
            for result in classify_segment(segment.text):
                classifications_to_add.append(
                    SegmentClassification(
                        review_id=review.id,
                        segment_id=segment.id,
                        clause_type=result["clause_type"],
                        confidence=result["confidence"],
                        method=result["method"],
                    )
                )
        if classifications_to_add:
            db.add_all(classifications_to_add)
            db.commit()
        db.execute(
            delete(ClauseEvaluation).where(ClauseEvaluation.review_id == review.id)
        )
        db.commit()

        evaluations: list[ClauseEvaluation] = []
        for clause_type in ClauseType:
            candidates = _select_candidate_segments(db, review.id, clause_type)
            if not candidates:
                result = evaluate_missing_clause(clause_type)
            else:
                segment_texts = [segment.text for segment in candidates]
                playbook_rules = get_rules_for_clause_type(clause_type)
                context = review.context_json or {}
                result = evaluate_clause(
                    clause_type, segment_texts, context, playbook_rules
                )

            evidence_spans = validate_evidence_spans(
                result.get("candidate_quotes", []), candidates
            )

            evaluations.append(
                ClauseEvaluation(
                    review_id=review.id,
                    clause_type=clause_type,
                    risk_label=RiskLabel(result["risk_label"]),
                    short_reason=result["short_reason"],
                    suggested_change=result["suggested_change"],
                    triggered_rule_ids=result.get("triggered_rule_ids", []),
                    evidence_spans=evidence_spans,
                )
            )

        if evaluations:
            db.add_all(evaluations)
            db.commit()
        # Pipeline steps will be added in later tasks.
    except Exception as exc:
        if review is not None:
            try:
                assert_transition(review.status, ReviewStatus.FAILED)
                review.status = ReviewStatus.FAILED
            except InvalidStatusTransition:
                pass
            review.error_message = str(exc)
            db.add(review)
            db.commit()
    finally:
        db.close()


def _select_candidate_segments(
    db: Session,
    review_id: UUID,
    clause_type: ClauseType,
    top_n: int = 5,
) -> list[ReviewSegment]:
    return (
        db.execute(
            select(ReviewSegment)
            .join(
                SegmentClassification,
                SegmentClassification.segment_id == ReviewSegment.id,
            )
            .where(
                SegmentClassification.review_id == review_id,
                SegmentClassification.clause_type == clause_type,
            )
            .order_by(
                SegmentClassification.confidence.desc(),
                ReviewSegment.segment_index.asc(),
            )
            .limit(top_n)
        )
        .scalars()
        .all()
    )
