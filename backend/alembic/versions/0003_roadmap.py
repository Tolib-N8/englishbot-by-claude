"""add roadmap to assessments

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("assessments") as batch:
        batch.add_column(sa.Column("roadmap_json", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("target_band", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("assessments") as batch:
        batch.drop_column("roadmap_json")
        batch.drop_column("target_band")
