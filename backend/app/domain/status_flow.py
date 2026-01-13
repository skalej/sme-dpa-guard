from app.domain.errors import InvalidStatusTransition
from app.models.review import ReviewStatus

ALLOWED_TRANSITIONS = {
    ReviewStatus.CREATED: {ReviewStatus.UPLOADED},
    ReviewStatus.UPLOADED: {ReviewStatus.PROCESSING},
    ReviewStatus.PROCESSING: {ReviewStatus.COMPLETED, ReviewStatus.FAILED},
    ReviewStatus.COMPLETED: set(),
    ReviewStatus.FAILED: set(),
}


def assert_transition(old_status: ReviewStatus, new_status: ReviewStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        raise InvalidStatusTransition(old_status, new_status)
