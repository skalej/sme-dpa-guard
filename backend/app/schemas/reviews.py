from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.review import ReviewStatus


class ReviewCreate(BaseModel):
    context_json: dict[str, Any] | None = None


class ReviewOut(BaseModel):
    review_id: UUID
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime
    context_json: dict[str, Any] | None = None
