from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.review import ReviewStatus


class ReviewCreate(BaseModel):
    context_json: dict[str, Any] | None = None


class ReviewDoc(BaseModel):
    filename: str | None = None
    mime: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    storage_key: str | None = None


class EvidenceSpanOut(BaseModel):
    segment_id: int
    quote: str
    page_start: int | None = None
    page_end: int | None = None


class ClauseEvaluationOut(BaseModel):
    clause_type: str
    risk_label: str
    short_reason: str
    suggested_change: str
    triggered_rule_ids: list[str]
    evidence_spans: list[EvidenceSpanOut]


class ReviewExplainOut(BaseModel):
    review_id: str
    status: str
    playbook_version: str
    decision: str | None = None
    summary: dict | None = None
    evaluations: list[ClauseEvaluationOut]


class ReviewOut(BaseModel):
    review_id: UUID
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime
    context_json: dict[str, Any] | None = None
    doc: ReviewDoc | None = None


class ReviewUploadOut(BaseModel):
    review_id: UUID
    status: ReviewStatus
    doc: ReviewDoc
