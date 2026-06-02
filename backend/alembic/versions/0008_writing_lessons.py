"""writing lessons

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "writing_lessons",
        sa.Column("slug", sa.String(), primary_key=True),
        sa.Column("body_md", sa.Text(), nullable=False),
        sa.Column(
            "generated_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("writing_lessons")
