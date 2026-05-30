from datetime import datetime

from pydantic import BaseModel


class PronunciationWord(BaseModel):
    word: str
    status: str  # matched | missed | substituted
    heard: str | None = None


class PronunciationResult(BaseModel):
    id: int
    target_text: str
    transcript: str
    overall_score: float
    per_word: list[PronunciationWord]
    tip_ru: str | None
    created_at: datetime


class PracticePhrase(BaseModel):
    phrase: str
