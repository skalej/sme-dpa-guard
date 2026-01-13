"""create clause evaluations table

Revision ID: 0007_clause_eval
Revises: 0006_seg_classify
Create Date: 2025-02-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007_clause_eval"
down_revision: Union[str, None] = "0006_seg_classify"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


RISK_LABEL = postgresql.ENUM("GREEN", "YELLOW", "RED", name="risk_label", create_type=False)
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
    RISK_LABEL.create(bind, checkfirst=True)
    CLAUSE_TYPE.create(bind, checkfirst=True)

    op.create_table(
        "clause_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reviews.id"),
            nullable=False,
        ),
        sa.Column("clause_type", CLAUSE_TYPE, nullable=False),
        sa.Column("risk_label", RISK_LABEL, nullable=False),
        sa.Column("short_reason", sa.Text(), nullable=False),
        sa.Column("suggested_change", sa.Text(), nullable=False),
        sa.Column(
            "triggered_rule_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "evidence_spans",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
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
        sa.UniqueConstraint(
            "review_id",
            "clause_type",
            name="uq_clause_evaluations_review_clause",
        ),
    )
    op.create_index("ix_clause_evaluations_review_id", "clause_evaluations", ["review_id"])
    op.create_index("ix_clause_evaluations_clause_type", "clause_evaluations", ["clause_type"])


def downgrade() -> None:
    op.drop_index("ix_clause_evaluations_clause_type", table_name="clause_evaluations")
    op.drop_index("ix_clause_evaluations_review_id", table_name="clause_evaluations")
    op.drop_table("clause_evaluations")
    bind = op.get_bind()
    RISK_LABEL.drop(bind, checkfirst=True)
