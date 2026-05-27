from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FlashcardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vocabulary_id: int
    ease: float
    interval_days: int
    repetitions: int
    due_date: datetime
    last_reviewed_at: datetime | None
    lapses: int
    suspended: bool


class FlashcardWithVocab(FlashcardOut):
    word_en: str
    translation_ru: str
    example_en: str | None = None
    example_ru: str | None = None
    part_of_speech: str | None = None


class ReviewRequest(BaseModel):
    quality: Literal[0, 3, 4, 5] = Field(
        description="0 = Again, 3 = Hard, 4 = Good, 5 = Easy"
    )


class FlashcardStats(BaseModel):
    total: int
    due_now: int
    reviewed_today: int
    new_today: int
