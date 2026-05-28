"""grammar exercises

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grammar_exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=False, server_default="B1"),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("prompt_ru", sa.Text(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("alternatives_json", sa.JSON(), nullable=True),
        sa.Column("choices_json", sa.JSON(), nullable=True),
        sa.Column("explanation_ru", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
    )
    op.create_index("ix_grammar_exercises_topic", "grammar_exercises", ["topic"])

    op.create_table(
        "exercise_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("grammar_exercises.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("feedback_ru", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
    )
    op.create_index("ix_exercise_attempts_exercise_id", "exercise_attempts", ["exercise_id"])


def downgrade() -> None:
    op.drop_index("ix_exercise_attempts_exercise_id", table_name="exercise_attempts")
    op.drop_table("exercise_attempts")
    op.drop_index("ix_grammar_exercises_topic", table_name="grammar_exercises")
    op.drop_table("grammar_exercises")
