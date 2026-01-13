"""add review job fields

Revision ID: 0009_review_job_fields
Revises: 0008_review_summary
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009_review_job_fields"
down_revision: Union[str, None] = "0008_review_summary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("job_id", sa.String(length=128), nullable=True))
    op.add_column(
        "reviews", sa.Column("job_status", sa.String(length=32), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("reviews", "job_status")
    op.drop_column("reviews", "job_id")
