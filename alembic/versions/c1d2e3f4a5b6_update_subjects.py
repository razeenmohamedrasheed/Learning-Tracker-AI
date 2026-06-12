"""update subjects status column and add missing constraints and indexes

Revision ID: c1d2e3f4a5b6
Revises: b499d592ead4
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b499d592ead4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE subjects SET status = 'in_progress' WHERE status = 'active'")
    # -------------------------------------------------------
    # subjects — alter status column
    # String(20) → String(30) to fit "partially_completed"
    # -------------------------------------------------------
    op.alter_column(
        "subjects",
        "status",
        existing_type=sa.String(20),
        type_=sa.String(30),
        nullable=False,
        server_default="in_progress",
    )

    # -------------------------------------------------------
    # subjects — add status_updated_at column
    # tracks when user last manually changed status
    # used to detect stale status after topic mutations
    # -------------------------------------------------------
    op.add_column(
        "subjects",
        sa.Column(
            "status_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # -------------------------------------------------------
    # subjects — check constraint on status values
    # -------------------------------------------------------
    op.create_check_constraint(
        "ck_subjects_status",
        "subjects",
        "status IN ('in_progress', 'completed', 'failed', 'partially_completed')",
    )

    # -------------------------------------------------------
    # subjects — check constraint on date range
    # -------------------------------------------------------
    op.create_check_constraint(
        "ck_subjects_date_range",
        "subjects",
        "end_date > start_date",
    )

    # -------------------------------------------------------
    # subjects — index on user_id
    # -------------------------------------------------------
    op.create_index("ix_subjects_user_id", "subjects", ["user_id"])

    # -------------------------------------------------------
    # subject_topics — fix is_completed to NOT NULL
    # -------------------------------------------------------
    op.alter_column(
        "subject_topics",
        "is_completed",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    )

    # -------------------------------------------------------
    # subject_topics — check constraint on percentage range
    # -------------------------------------------------------
    op.create_check_constraint(
        "ck_subject_topics_percentage_range",
        "subject_topics",
        "target_percentage >= 0 AND target_percentage <= 100",
    )

    # -------------------------------------------------------
    # subject_topics — indexes
    # -------------------------------------------------------
    op.create_index("ix_subject_topics_subject_id", "subject_topics", ["subject_id"])
    op.create_index("ix_subject_topics_user_id",    "subject_topics", ["user_id"])


def downgrade() -> None:

    # reverse order — remove newest changes first

    op.drop_index("ix_subject_topics_user_id",    table_name="subject_topics")
    op.drop_index("ix_subject_topics_subject_id", table_name="subject_topics")

    op.drop_constraint("ck_subject_topics_percentage_range", "subject_topics", type_="check")

    op.alter_column(
        "subject_topics",
        "is_completed",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )

    op.drop_index("ix_subjects_user_id", table_name="subjects")

    op.drop_constraint("ck_subjects_date_range", "subjects", type_="check")
    op.drop_constraint("ck_subjects_status",     "subjects", type_="check")

    op.drop_column("subjects", "status_updated_at")

    op.alter_column(
        "subjects",
        "status",
        existing_type=sa.String(30),
        type_=sa.String(20),
        nullable=True,
        server_default="active",
    )