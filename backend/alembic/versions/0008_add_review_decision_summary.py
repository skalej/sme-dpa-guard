"""add review decision and summary

Revision ID: 0008_review_summary
Revises: 0007_clause_eval
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0008_review_summary"
down_revision: Union[str, None] = "0007_clause_eval"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("decision", sa.String(length=64), nullable=True))
    op.add_column("reviews", sa.Column("summary_json", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "summary_json")
    op.drop_column("reviews", "decision")
