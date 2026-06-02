from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

TaskType = Literal["task1_academic", "task2"]


class WritingPromptOut(BaseModel):
    task_type: str
    prompt_en: str
    prompt_ru: str | None
    min_words: int


class WritingPromptRequest(BaseModel):
    task_type: TaskType = "task2"


class WritingSubmitRequest(BaseModel):
    task_type: TaskType
    prompt_en: str
    prompt_ru: str | None = None
    min_words: int
    user_text: str


class WritingCriterion(BaseModel):
    name: str
    band: str | None = None
    comment_ru: str | None = None


class WritingCorrection(BaseModel):
    original: str
    fixed: str
    explanation_ru: str | None = None


class WritingResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: str
    prompt_en: str
    prompt_ru: str | None
    min_words: int
    user_text: str
    word_count: int
    overall_band: str | None
    criteria: list[WritingCriterion]
    corrections: list[WritingCorrection]
    tip_ru: str | None
    created_at: datetime


class WritingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_type: str
    word_count: int
    overall_band: str | None
    created_at: datetime


class LessonSummary(BaseModel):
    slug: str
    title: str
    summary: str
    order: int
    read: bool
    generated: bool


class LessonDetail(BaseModel):
    slug: str
    title: str
    summary: str
    order: int
    body_md: str
    read: bool
    generated_at: datetime
    next_slug: str | None
    prev_slug: str | None


class TemplateSummary(BaseModel):
    slug: str
    title: str
    summary: str
    order: int
    generated: bool


class TemplateDetail(BaseModel):
    slug: str
    title: str
    summary: str
    order: int
    body_md: str
    generated_at: datetime
    next_slug: str | None
    prev_slug: str | None
