from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class ReviewStatus(str, Enum):
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ReviewOut(BaseModel):
    review_id: UUID
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime
