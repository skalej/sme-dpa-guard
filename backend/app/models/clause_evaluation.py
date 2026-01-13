from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models.clause_type import ClauseType
from app.models.risk_label import RiskLabel


class ClauseEvaluation(Base):
    __tablename__ = "clause_evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False, index=True
    )
    clause_type: Mapped[ClauseType] = mapped_column(
        SAEnum(ClauseType, name="clause_type", create_type=False), nullable=False
    )
    risk_label: Mapped[RiskLabel] = mapped_column(
        SAEnum(RiskLabel, name="risk_label", create_type=False), nullable=False
    )
    short_reason: Mapped[str] = mapped_column(nullable=False)
    suggested_change: Mapped[str] = mapped_column(nullable=False)
    triggered_rule_ids: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    evidence_spans: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "uq_clause_evaluations_review_clause",
            "review_id",
            "clause_type",
            unique=True,
        ),
    )
