from fastapi import APIRouter

from app.api.v1 import chat, conversations, exercises, flashcards, meta, notes, vocab

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(meta.router, tags=["meta"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(vocab.router, prefix="/vocab", tags=["vocab"])
api_router.include_router(flashcards.router, prefix="/flashcards", tags=["flashcards"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(exercises.router, prefix="/exercises", tags=["exercises"])
