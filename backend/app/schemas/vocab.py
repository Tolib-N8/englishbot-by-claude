from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VocabularyBase(BaseModel):
    word_en: str
    lemma_en: str | None = None
    translation_ru: str
    example_en: str | None = None
    example_ru: str | None = None
    part_of_speech: str | None = None
    cefr_level: str | None = None
    notes: str | None = None


class VocabularyCreate(VocabularyBase):
    source: str | None = "manual"


class VocabularyOut(VocabularyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str | None
    created_at: datetime
    has_flashcard: bool = False


class VocabExtractRequest(BaseModel):
    message_id: int


class VocabExtractResult(BaseModel):
    created: list[VocabularyOut]
    skipped_existing: list[str]
