"""pronunciation attempts

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pronunciation_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("target_text", sa.Text(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("per_word_json", sa.JSON(), nullable=True),
        sa.Column("tip_ru", sa.Text(), nullable=True),
        sa.Column("audio_path", sa.String(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
    )


def downgrade() -> None:
    op.drop_table("pronunciation_attempts")
