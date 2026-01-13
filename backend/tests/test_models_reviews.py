from app.models.review import ReviewStatus


def test_review_status_values() -> None:
    assert [status.value for status in ReviewStatus] == [
        "CREATED",
        "UPLOADED",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
    ]
