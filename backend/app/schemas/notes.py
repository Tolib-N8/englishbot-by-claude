from pydantic import BaseModel


class NoteSummary(BaseModel):
    path: str
    folder: str
    name: str
    title: str
    type: str | None = None
    cefr: str | None = None
    date: str | None = None


class NoteDetail(NoteSummary):
    frontmatter: dict
    body: str
    links: list[str]


class SummarizeResponse(BaseModel):
    confirmation: str
    new_note_paths: list[str]
    cards_added: int = 0
