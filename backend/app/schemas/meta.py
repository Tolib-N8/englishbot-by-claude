from pydantic import BaseModel


class Settings(BaseModel):
    level: str
    native_language: str
    model: str


class SettingsUpdate(BaseModel):
    level: str | None = None


class LevelOut(BaseModel):
    level: str
    declared_level: str
    estimated_level: str
    next_level: str | None
    progress_to_next: int
    points: float
    words_total: int
    words_mastered: int
    topics: int
    sessions: int
