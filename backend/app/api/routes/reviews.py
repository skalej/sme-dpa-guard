import json
from typing import Optional
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.celery_app import celery_app
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
from app.workers.celery_tasks import process_review_task

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
        decision=review.decision,
        summary=review.summary_json,
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
    db: Session = Depends(get_db),
) -> dict:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != ReviewStatus.UPLOADED:
        raise HTTPException(status_code=400, detail="Review not ready for processing")

    assert_transition(review.status, ReviewStatus.PROCESSING)
    review.status = ReviewStatus.PROCESSING
    db.add(review)
    db.commit()
    db.refresh(review)

    async_result = process_review_task.delay(str(review.id))
    review.job_id = async_result.id
    review.job_status = getattr(async_result, "status", None) or "PENDING"
    db.add(review)
    db.commit()

    return {
        "message": "Processing started",
        "review_id": str(review.id),
        "status": review.status.value,
        "job_id": async_result.id,
    }


@router.post("/submit")
def submit_review(
    file: UploadFile | None = File(None),
    context_json: str | None = Form(None),
    company_role: str | None = Form(None),
    region: str | None = Form(None),
    vendor_type: str | None = Form(None),
    db: Session = Depends(get_db),
) -> dict:
    if file is None:
        raise HTTPException(status_code=400, detail="Missing file")

    if context_json:
        try:
            parsed = json.loads(context_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid context_json") from exc
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=400, detail="Invalid context_json")
        payload = parsed
    else:
        if not company_role or not region:
            raise HTTPException(status_code=400, detail="Missing context fields")
        payload = {
            "company_role": company_role,
            "region": region,
            "vendor_type": vendor_type or None,
        }

    review = Review(status=ReviewStatus.CREATED, context_json=payload)
    db.add(review)
    db.commit()
    db.refresh(review)

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

    try:
        assert_transition(updated.status, ReviewStatus.PROCESSING)
        updated.status = ReviewStatus.PROCESSING
        db.add(updated)
        db.commit()
        db.refresh(updated)

        async_result = process_review_task.delay(str(updated.id))
        updated.job_id = async_result.id
        updated.job_status = getattr(async_result, "status", None) or "PENDING"
        db.add(updated)
        db.commit()
    except Exception as exc:
        try:
            assert_transition(updated.status, ReviewStatus.FAILED)
            updated.status = ReviewStatus.FAILED
        except InvalidStatusTransition:
            pass
        updated.error_message = str(exc)
        db.add(updated)
        db.commit()
        raise HTTPException(status_code=503, detail="Failed to enqueue job") from exc

    return {
        "review_id": str(updated.id),
        "job_id": updated.job_id,
        "status": "processing",
    }


@router.get("/{review_id}/job")
def get_job_status(review_id: UUID, db: Session = Depends(get_db)) -> dict:
    review = db.get(Review, review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    if not review.job_id:
        return {"review_id": str(review.id), "job_id": None, "state": None}

    result = AsyncResult(review.job_id, app=celery_app)
    review.job_status = result.state
    db.add(review)
    db.commit()

    return {
        "review_id": str(review.id),
        "job_id": review.job_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
    }
