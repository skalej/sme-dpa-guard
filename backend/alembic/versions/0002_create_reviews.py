"""create reviews table

Revision ID: 0002_create_reviews
Revises: 0001_baseline
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_create_reviews"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REVIEW_STATUS = postgresql.ENUM(
    "CREATED",
    "UPLOADED",
    "PROCESSING",
    "COMPLETED",
    "FAILED",
    name="review_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    REVIEW_STATUS.create(bind, checkfirst=True)

    op.create_table(
        "reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("status", REVIEW_STATUS, nullable=False),
        sa.Column("context_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("reviews")
    REVIEW_STATUS.drop(bind, checkfirst=True)
