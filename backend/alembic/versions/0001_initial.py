"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("display_name", sa.String(), nullable=False, server_default="me"),
        sa.Column("level", sa.String(), nullable=False, server_default="A1"),
        sa.Column("native_language", sa.String(), nullable=False, server_default="ru"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("mode", sa.String(), nullable=False, server_default="free_chat"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("corrections_json", sa.JSON(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "vocabulary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("word_en", sa.String(), nullable=False),
        sa.Column("lemma_en", sa.String(), nullable=True),
        sa.Column("translation_ru", sa.String(), nullable=False),
        sa.Column("example_en", sa.Text(), nullable=True),
        sa.Column("example_ru", sa.Text(), nullable=True),
        sa.Column("part_of_speech", sa.String(), nullable=True),
        sa.Column("cefr_level", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("word_en", name="uq_vocabulary_word_en"),
    )

    op.create_table(
        "flashcards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "vocabulary_id",
            sa.Integer(),
            sa.ForeignKey("vocabulary.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ease", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "due_date",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("last_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("lapses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("suspended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("vocabulary_id", name="uq_flashcards_vocab"),
    )
    op.create_index("ix_flashcards_due_date", "flashcards", ["due_date"])


def downgrade() -> None:
    op.drop_index("ix_flashcards_due_date", table_name="flashcards")
    op.drop_table("flashcards")
    op.drop_table("vocabulary")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
