"""writing submissions

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "writing_submissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_type", sa.String(), nullable=False),  # task1_academic|task1_general|task2
        sa.Column("prompt_en", sa.Text(), nullable=False),
        sa.Column("prompt_ru", sa.Text(), nullable=True),
        sa.Column("min_words", sa.Integer(), nullable=False, server_default="150"),
        sa.Column("user_text", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_band", sa.String(), nullable=True),  # "5.5"
        sa.Column("criteria_json", sa.JSON(), nullable=True),   # 4 IELTS criteria
        sa.Column("corrections_json", sa.JSON(), nullable=True),  # inline error fixes
        sa.Column("tip_ru", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
    )


def downgrade() -> None:
    op.drop_table("writing_submissions")
