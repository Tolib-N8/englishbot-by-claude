from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WritingSubmission(Base):
    __tablename__ = "writing_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_type: Mapped[str] = mapped_column(String, nullable=False)
    prompt_en: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_words: Mapped[int] = mapped_column(Integer, nullable=False, default=150)
    user_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_band: Mapped[str | None] = mapped_column(String, nullable=True)
    criteria_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    corrections_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    tip_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
