from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.errors import InvalidStatusTransition
from app.domain.status_flow import assert_transition
from app.models.review import Review, ReviewStatus


def process_review(review_id: UUID) -> None:
    db: Session = SessionLocal()
    review: Review | None = None
    try:
        review = db.get(Review, review_id)
        if review is None:
            return
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
