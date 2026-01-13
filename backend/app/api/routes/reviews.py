from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.review import Review, ReviewStatus
from app.schemas.reviews import ReviewCreate, ReviewOut

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _to_review_out(review: Review) -> ReviewOut:
    return ReviewOut(
        review_id=review.id,
        status=review.status,
        created_at=review.created_at,
        updated_at=review.updated_at,
        context_json=review.context_json,
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
