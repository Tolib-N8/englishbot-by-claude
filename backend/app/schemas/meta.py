from pydantic import BaseModel


class Settings(BaseModel):
    level: str
    native_language: str
    model: str


class SettingsUpdate(BaseModel):
    level: str | None = None


class Skill(BaseModel):
    name: str
    cefr: str | None = None
    ielts: str | None = None
    comment_ru: str | None = None


class Evidence(BaseModel):
    quote: str
    issue_ru: str | None = None


class RoadmapPhase(BaseModel):
    title: str
    skill: str | None = None
    target_ru: str | None = None
    actions_ru: list[str] = []
    est_weeks: int | None = None


class AssessmentOut(BaseModel):
    cefr_level: str
    ielts_band: str | None
    confidence: str
    summary_ru: str
    skills: list[Skill]
    strengths: list[str]
    weaknesses: list[str]
    next_steps: list[str]
    evidence: list[Evidence]
    roadmap: list[RoadmapPhase]
    target_band: str | None
    based_on_messages: int
    based_on_words: int
    created_at: str


class LevelOut(BaseModel):
    assessment: AssessmentOut | None
    words_total: int
    words_mastered: int
    topics: int
    sessions: int
    conversations: int
