from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.errors import InvalidStatusTransition
from app.models.review import Review, ReviewStatus
from app.schemas.reviews import ReviewCreate, ReviewDoc, ReviewOut, ReviewUploadOut
from app.services.uploads import UnsupportedFileType, upload_review_document

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
