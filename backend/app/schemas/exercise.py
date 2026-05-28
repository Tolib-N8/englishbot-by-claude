from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ExerciseType = Literal["fill_blank", "mcq", "translate_ru_en", "translate_en_ru"]


class GenerateRequest(BaseModel):
    topic: str
    count: int = Field(default=8, ge=1, le=20)
    types: list[ExerciseType] | None = None


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    level: str
    type: str
    prompt: str
    prompt_ru: str | None
    choices_json: list | None
    # answer + explanation are NOT exposed until after an attempt
    created_at: datetime
    attempted: bool = False
    last_correct: bool | None = None


class AttemptRequest(BaseModel):
    user_answer: str


class AttemptResult(BaseModel):
    is_correct: bool
    feedback_ru: str | None
    answer: str
    explanation_ru: str | None


class TopicSuggestion(BaseModel):
    topic: str
    source: str  # "roadmap" | "common"


class ExerciseStats(BaseModel):
    total: int
    attempted: int
    correct: int
    accuracy: int  # percent
