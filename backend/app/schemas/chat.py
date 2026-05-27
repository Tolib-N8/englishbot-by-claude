from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class Correction(BaseModel):
    original: str
    fixed: str
    explanation_ru: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    corrections_json: list[Any] | None = None
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    mode: str
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    title: str | None = None
    mode: str = "free_chat"


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class ChatStreamRequest(BaseModel):
    conversation_id: int
    content: str
