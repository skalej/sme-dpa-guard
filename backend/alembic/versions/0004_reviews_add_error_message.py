"""add error message to reviews

Revision ID: 0004_reviews_add_error_message
Revises: 0003_reviews_add_doc_fields
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_reviews_add_error_message"
down_revision: Union[str, None] = "0003_reviews_add_doc_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("error_message", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "error_message")
