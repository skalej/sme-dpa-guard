from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from sqlalchemy import Enum as SAEnum

from app.models.clause_type import ClauseType


class SegmentClassification(Base):
    __tablename__ = "segment_classifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False, index=True
    )
    segment_id: Mapped[int] = mapped_column(
        ForeignKey("review_segments.id"), nullable=False, index=True
    )
    clause_type: Mapped[ClauseType] = mapped_column(
        SAEnum(ClauseType, name="clause_type", create_type=False), nullable=False
    )
    confidence: Mapped[float] = mapped_column(nullable=False)
    method: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "uq_segment_classifications_review_segment_clause",
            "review_id",
            "segment_id",
            "clause_type",
            unique=True,
        ),
    )
