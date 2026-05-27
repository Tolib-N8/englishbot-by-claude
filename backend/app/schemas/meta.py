from pydantic import BaseModel


class Settings(BaseModel):
    level: str
    native_language: str
    model: str


class SettingsUpdate(BaseModel):
    level: str | None = None
