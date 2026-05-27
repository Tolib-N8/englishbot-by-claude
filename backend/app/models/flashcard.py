from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Flashcard(Base):
    __tablename__ = "flashcards"
    __table_args__ = (UniqueConstraint("vocabulary_id", name="uq_flashcards_vocab"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vocabulary_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vocabulary.id", ondelete="CASCADE"),
        nullable=False,
    )
    ease: Mapped[float] = mapped_column(Float, nullable=False, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    due_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), index=True
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lapses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suspended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    vocabulary: Mapped["Vocabulary"] = relationship(  # noqa: F821
        "Vocabulary", back_populates="flashcard"
    )
