"""add review document fields

Revision ID: 0003_reviews_add_doc_fields
Revises: 0002_create_reviews
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_reviews_add_doc_fields"
down_revision: Union[str, None] = "0002_create_reviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("doc_filename", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("doc_mime", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("doc_size_bytes", sa.Integer(), nullable=True))
    op.add_column("reviews", sa.Column("doc_sha256", sa.Text(), nullable=True))
    op.add_column("reviews", sa.Column("doc_storage_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "doc_storage_key")
    op.drop_column("reviews", "doc_sha256")
    op.drop_column("reviews", "doc_size_bytes")
    op.drop_column("reviews", "doc_mime")
    op.drop_column("reviews", "doc_filename")
