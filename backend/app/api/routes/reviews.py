from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.errors import InvalidStatusTransition
from app.domain.status_flow import assert_transition
from app.models.clause_evaluation import ClauseEvaluation
from app.models.review import Review, ReviewStatus
from app.playbook.rules import get_playbook_version
from app.schemas.reviews import (
    ClauseEvaluationOut,
    EvidenceSpanOut,
    ReviewCreate,
    ReviewDoc,
    ReviewExplainOut,
    ReviewOut,
    ReviewUploadOut,
)
from app.services.uploads import UnsupportedFileType, upload_review_document
from app.workers.tasks import process_review

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _to_review_out(review: Review) -> ReviewOut:
    doc = None
    if review.doc_storage_key or review.doc_filename or review.doc_mime:
        doc = ReviewDoc(
            filename=review.doc_filename,
            mime=review.doc_mime,
            size_bytes=review.doc_size_bytes,
            sha256=review.doc_sha256,
            storage_key=review.doc_storage_key,
        )
    return ReviewOut(
        review_id=review.id,
        status=review.status,
        created_at=review.created_at,
        updated_at=review.updated_at,
        context_json=review.context_json,
        doc=doc,
    )


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: Optional[ReviewCreate] = None, db: Session = Depends(get_db)
) -> ReviewOut:
    review = Review(
        status=ReviewStatus.CREATED,
        context_json=payload.context_json if payload else None,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return _to_review_out(review)


@router.get("/{review_id}", response_model=ReviewOut)
def get_review(review_id: UUID, db: Session = Depends(get_db)) -> ReviewOut:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return _to_review_out(review)


@router.get("/{review_id}/explain", response_model=ReviewExplainOut)
def explain_review(review_id: UUID, db: Session = Depends(get_db)) -> ReviewExplainOut:
    return _build_explain_payload(review_id, db)


@router.get("/{review_id}/results", response_model=ReviewExplainOut)
def results_review(review_id: UUID, db: Session = Depends(get_db)) -> ReviewExplainOut:
    return _build_explain_payload(review_id, db)


def _build_explain_payload(review_id: UUID, db: Session) -> ReviewExplainOut:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    evaluations = (
        db.query(ClauseEvaluation)
        .filter(ClauseEvaluation.review_id == review_id)
        .order_by(ClauseEvaluation.clause_type)
        .all()
    )

    evaluation_out = []
    for evaluation in evaluations:
        evidence_spans = [
            EvidenceSpanOut(
                segment_id=span.get("segment_id"),
                quote=span.get("quote"),
                page_start=span.get("page_start"),
                page_end=span.get("page_end"),
            )
            for span in evaluation.evidence_spans or []
        ]
        evaluation_out.append(
            ClauseEvaluationOut(
                clause_type=evaluation.clause_type.value,
                risk_label=evaluation.risk_label.value,
                short_reason=evaluation.short_reason,
                suggested_change=evaluation.suggested_change,
                triggered_rule_ids=evaluation.triggered_rule_ids or [],
                evidence_spans=evidence_spans,
            )
        )

    return ReviewExplainOut(
        review_id=str(review.id),
        status=review.status.value,
        playbook_version=get_playbook_version(),
        evaluations=evaluation_out,
    )


@router.post("/{review_id}/upload", response_model=ReviewUploadOut)
def upload_review_file(
    review_id: UUID,
    file: UploadFile,
    db: Session = Depends(get_db),
) -> ReviewUploadOut:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != ReviewStatus.CREATED:
        raise HTTPException(status_code=409, detail="Review is not in CREATED status")

    try:
        data = file.file.read()
        updated = upload_review_document(
            db=db,
            review=review,
            content_type=file.content_type or "",
            filename=file.filename or "file",
            data=data,
        )
    except InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UnsupportedFileType as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    finally:
        file.file.close()

    doc = ReviewDoc(
        filename=updated.doc_filename,
        mime=updated.doc_mime,
        size_bytes=updated.doc_size_bytes,
        sha256=updated.doc_sha256,
        storage_key=updated.doc_storage_key,
    )
    return ReviewUploadOut(review_id=updated.id, status=updated.status, doc=doc)


@router.post("/{review_id}/start")
def start_processing(
    review_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != ReviewStatus.UPLOADED:
        raise HTTPException(status_code=409, detail="Review not ready for processing")

    assert_transition(review.status, ReviewStatus.PROCESSING)
    review.status = ReviewStatus.PROCESSING
    db.add(review)
    db.commit()
    db.refresh(review)

    background_tasks.add_task(process_review, review_id)

    return {
        "message": "Processing started",
        "review_id": str(review.id),
        "status": review.status.value,
    }
