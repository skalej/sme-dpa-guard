from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReviewSegment(Base):
    __tablename__ = "review_segments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False, index=True
    )
    segment_index: Mapped[int] = mapped_column(nullable=False, index=True)
    heading: Mapped[str | None] = mapped_column(nullable=True)
    section_number: Mapped[str | None] = mapped_column(nullable=True)
    text: Mapped[str] = mapped_column(nullable=False)
    hash: Mapped[str] = mapped_column(nullable=False)
    page_start: Mapped[int | None] = mapped_column(nullable=True)
    page_end: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("uq_review_segments_review_index", "review_id", "segment_index", unique=True),
    )
