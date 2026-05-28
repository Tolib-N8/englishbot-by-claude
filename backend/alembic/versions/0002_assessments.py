"""assessments table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("cefr_level", sa.String(), nullable=False),
        sa.Column("ielts_band", sa.String(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=False, server_default="low"),
        sa.Column("summary_ru", sa.Text(), nullable=True),
        sa.Column("skills_json", sa.JSON(), nullable=True),
        sa.Column("strengths_json", sa.JSON(), nullable=True),
        sa.Column("weaknesses_json", sa.JSON(), nullable=True),
        sa.Column("next_steps_json", sa.JSON(), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("based_on_messages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("based_on_words", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("assessments")
