"""create review segments table

Revision ID: 0005_create_review_segments
Revises: 0004_reviews_add_error_message
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_create_review_segments"
down_revision: Union[str, None] = "0004_reviews_add_error_message"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_segments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reviews.id"),
            nullable=False,
        ),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("heading", sa.String(length=255), nullable=True),
        sa.Column("section_number", sa.String(length=50), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("hash", sa.String(length=32), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.UniqueConstraint("review_id", "segment_index", name="uq_review_segments_review_index"),
    )
    op.create_index("ix_review_segments_review_id", "review_segments", ["review_id"])


def downgrade() -> None:
    op.drop_index("ix_review_segments_review_id", table_name="review_segments")
    op.drop_table("review_segments")
