from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vocabulary(Base):
    __tablename__ = "vocabulary"
    __table_args__ = (UniqueConstraint("word_en", name="uq_vocabulary_word_en"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    word_en: Mapped[str] = mapped_column(String, nullable=False)
    lemma_en: Mapped[str | None] = mapped_column(String, nullable=True)
    translation_ru: Mapped[str] = mapped_column(String, nullable=False)
    example_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    part_of_speech: Mapped[str | None] = mapped_column(String, nullable=True)
    cefr_level: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    flashcard: Mapped["Flashcard | None"] = relationship(  # noqa: F821
        "Flashcard", back_populates="vocabulary", uselist=False, cascade="all, delete-orphan"
    )
