from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    cefr_level: Mapped[str] = mapped_column(String, nullable=False)
    ielts_band: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[str] = mapped_column(String, nullable=False, default="low")
    summary_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    strengths_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weaknesses_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    next_steps_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    based_on_messages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    based_on_words: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
