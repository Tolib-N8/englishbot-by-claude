from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class WritingLesson(Base):
    __tablename__ = "writing_lessons"

    slug: Mapped[str] = mapped_column(String, primary_key=True)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
