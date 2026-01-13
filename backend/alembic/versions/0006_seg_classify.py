"""create segment classifications table

Revision ID: 0006_seg_classify
Revises: 0005_create_review_segments
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006_seg_classify"
down_revision: Union[str, None] = "0005_create_review_segments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CLAUSE_TYPE = postgresql.ENUM(
    "ROLES",
    "SUBJECT_DURATION",
    "PURPOSE_NATURE",
    "DATA_CATEGORIES_SUBJECTS",
    "SECURITY_TOMS",
    "SUBPROCESSORS",
    "TRANSFERS",
    "BREACH_NOTIFICATION",
    "DSAR_ASSISTANCE",
    "DELETION_RETURN",
    "AUDIT_RIGHTS",
    "CONFIDENTIALITY",
    "LIABILITY",
    "GOVERNING_LAW",
    "ORDER_OF_PRECEDENCE",
    name="clause_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    CLAUSE_TYPE.create(bind, checkfirst=True)
    inspector = sa.inspect(bind)
    if not inspector.has_table("segment_classifications"):
        op.create_table(
            "segment_classifications",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column(
                "review_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("reviews.id"),
                nullable=False,
            ),
            sa.Column(
                "segment_id",
                sa.Integer(),
                sa.ForeignKey("review_segments.id"),
                nullable=False,
            ),
            sa.Column("clause_type", CLAUSE_TYPE, nullable=False),
            sa.Column("confidence", sa.Float(), nullable=False),
            sa.Column("method", sa.String(length=16), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "review_id",
                "segment_id",
                "clause_type",
                name="uq_segment_classifications_review_segment_clause",
            ),
        )
        op.create_index(
            "ix_segment_classifications_review_id",
            "segment_classifications",
            ["review_id"],
        )
        op.create_index(
            "ix_segment_classifications_segment_id",
            "segment_classifications",
            ["segment_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("segment_classifications"):
        op.drop_index(
            "ix_segment_classifications_segment_id", table_name="segment_classifications"
        )
        op.drop_index(
            "ix_segment_classifications_review_id", table_name="segment_classifications"
        )
        op.drop_table("segment_classifications")
    CLAUSE_TYPE.drop(bind, checkfirst=True)
