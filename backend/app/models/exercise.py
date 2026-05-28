from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GrammarExercise(Base):
    __tablename__ = "grammar_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic: Mapped[str] = mapped_column(String, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String, nullable=False, default="B1")
    type: Mapped[str] = mapped_column(String, nullable=False)  # fill_blank|mcq|translate_ru_en|translate_en_ru
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    alternatives_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    choices_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    explanation_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    attempts: Mapped[list["ExerciseAttempt"]] = relationship(
        "ExerciseAttempt",
        back_populates="exercise",
        cascade="all, delete-orphan",
        order_by="ExerciseAttempt.created_at",
    )


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("grammar_exercises.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feedback_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    exercise: Mapped["GrammarExercise"] = relationship("GrammarExercise", back_populates="attempts")
