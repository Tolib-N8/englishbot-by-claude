"""Pronunciation API: record audio → Whisper transcript → score → Russian tip."""
from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import DATA_DIR
from app.database import get_db
from app.deps import get_or_create_singleton_user
from app.models.pronunciation import PronunciationAttempt
from app.schemas.pronunciation import (
    PracticePhrase,
    PronunciationResult,
    PronunciationWord,
)
from app.services.pronunciation import generate_phrase, score_attempt
from app.services.transcription import transcribe

router = APIRouter()

AUDIO_DIR = DATA_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _to_out(a: PronunciationAttempt) -> PronunciationResult:
    return PronunciationResult(
        id=a.id,
        target_text=a.target_text,
        transcript=a.transcript,
        overall_score=a.overall_score,
        per_word=[PronunciationWord(**w) for w in (a.per_word_json or [])],
        tip_ru=a.tip_ru,
        created_at=a.created_at,
    )


@router.get("/practice", response_model=PracticePhrase)
async def practice(
    focus: str | None = Query(None, description="Optional sound to target, e.g. 'θ'"),
    db: AsyncSession = Depends(get_db),
):
    user = await get_or_create_singleton_user(db)
    return PracticePhrase(phrase=await generate_phrase(user.level, focus))


@router.post("/transcribe", response_model=PronunciationResult)
async def transcribe_audio(
    audio: UploadFile = File(...),
    target_text: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if not target_text.strip():
        raise HTTPException(400, "target_text required")

    # Persist the upload (so the user can replay later).
    suffix = Path(audio.filename or "rec.bin").suffix or ".webm"
    audio_path = AUDIO_DIR / f"{uuid.uuid4().hex}{suffix}"
    with audio_path.open("wb") as f:
        shutil.copyfileobj(audio.file, f)

    # Whisper is CPU-bound; run in a worker thread.
    transcript = await asyncio.to_thread(transcribe, str(audio_path))
    result = await score_attempt(target_text, transcript)

    rec = PronunciationAttempt(
        target_text=target_text,
        transcript=result.transcript,
        overall_score=result.overall_score,
        per_word_json=result.per_word,
        tip_ru=result.tip_ru,
        audio_path=str(audio_path.relative_to(DATA_DIR)),
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return _to_out(rec)


@router.get("", response_model=list[PronunciationResult])
async def history(limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(PronunciationAttempt)
            .order_by(PronunciationAttempt.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [_to_out(r) for r in rows]
