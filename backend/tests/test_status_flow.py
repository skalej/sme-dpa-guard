import pytest

from app.domain.errors import InvalidStatusTransition
from app.domain.status_flow import assert_transition
from app.models.review import ReviewStatus


@pytest.mark.parametrize(
    "old_status,new_status",
    [
        (ReviewStatus.CREATED, ReviewStatus.UPLOADED),
        (ReviewStatus.UPLOADED, ReviewStatus.PROCESSING),
        (ReviewStatus.PROCESSING, ReviewStatus.COMPLETED),
        (ReviewStatus.PROCESSING, ReviewStatus.FAILED),
    ],
)
def test_allows_valid_transitions(old_status, new_status) -> None:
    assert_transition(old_status, new_status)


@pytest.mark.parametrize(
    "old_status,new_status",
    [
        (ReviewStatus.CREATED, ReviewStatus.PROCESSING),
        (ReviewStatus.UPLOADED, ReviewStatus.COMPLETED),
        (ReviewStatus.COMPLETED, ReviewStatus.FAILED),
        (ReviewStatus.FAILED, ReviewStatus.PROCESSING),
    ],
)
def test_rejects_invalid_transitions(old_status, new_status) -> None:
    with pytest.raises(InvalidStatusTransition) as exc_info:
        assert_transition(old_status, new_status)

    message = str(exc_info.value)
    assert str(old_status) in message
    assert str(new_status) in message
