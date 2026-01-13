from app.celery_app import celery_app
from app.workers.tasks import process_review


@celery_app.task(
    name="reviews.process_review",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def process_review_task(self, review_id: str):
    try:
        return process_review(review_id)
    except Exception as exc:
        raise self.retry(exc=exc)
