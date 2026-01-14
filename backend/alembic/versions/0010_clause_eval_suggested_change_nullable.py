"""make clause_evaluations.suggested_change nullable

Revision ID: 0010_clause_eval_suggested
Revises: 0009_review_job_fields
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0010_clause_eval_suggested"
down_revision: Union[str, None] = "0009_review_job_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "clause_evaluations",
        "suggested_change",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "clause_evaluations",
        "suggested_change",
        existing_type=sa.Text(),
        nullable=False,
    )
