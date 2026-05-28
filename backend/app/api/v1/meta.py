from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_or_create_singleton_user
from app.models.assessment import Assessment
from app.models.conversation import Conversation
from app.models.flashcard import Flashcard
from app.models.message import Message
from app.models.vocabulary import Vocabulary
from app.schemas.meta import (
    AssessmentOut,
    LevelOut,
    Settings as SettingsSchema,
    SettingsUpdate,
)
from app.services.assessor import assess_writing
from app.services.vault import list_notes

router = APIRouter()


@router.get("/settings", response_model=SettingsSchema)
async def get_settings(db: AsyncSession = Depends(get_db)):
    user = await get_or_create_singleton_user(db)
    return SettingsSchema(
        level=user.level,
        native_language=user.native_language,
        model=settings.claude_model or "claude-code-default",
    )


@router.patch("/settings", response_model=SettingsSchema)
async def update_settings(body: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    user = await get_or_create_singleton_user(db)
    if body.level:
        user.level = body.level
    await db.commit()
    await db.refresh(user)
    return SettingsSchema(
        level=user.level,
        native_language=user.native_language,
        model=settings.claude_model or "claude-code-default",
    )


async def _activity_signals(db: AsyncSession) -> dict[str, int]:
    words = (await db.execute(select(func.count(Vocabulary.id)))).scalar_one()
    mastered = (
        await db.execute(select(func.count(Flashcard.id)).where(Flashcard.repetitions >= 2))
    ).scalar_one()
    convos = (await db.execute(select(func.count(Conversation.id)))).scalar_one()
    topics = len(list_notes("topics"))
    sessions = len(list_notes("sessions"))
    return {
        "words_total": int(words),
        "words_mastered": int(mastered),
        "topics": int(topics),
        "sessions": int(sessions),
        "conversations": int(convos),
    }


def _to_out(a: Assessment) -> AssessmentOut:
    return AssessmentOut(
        cefr_level=a.cefr_level,
        ielts_band=a.ielts_band,
        confidence=a.confidence,
        summary_ru=a.summary_ru or "",
        skills=a.skills_json or [],
        strengths=a.strengths_json or [],
        weaknesses=a.weaknesses_json or [],
        next_steps=a.next_steps_json or [],
        evidence=a.evidence_json or [],
        roadmap=a.roadmap_json or [],
        target_band=a.target_band,
        based_on_messages=a.based_on_messages,
        based_on_words=a.based_on_words,
        created_at=a.created_at.isoformat(),
    )


@router.get("/level", response_model=LevelOut)
async def get_level(db: AsyncSession = Depends(get_db)):
    signals = await _activity_signals(db)
    latest = (
        await db.execute(select(Assessment).order_by(Assessment.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    return LevelOut(
        assessment=_to_out(latest) if latest else None,
        **signals,
    )


@router.post("/level/assess", response_model=LevelOut)
async def assess_level(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Message.content)
            .where(Message.role == "user")
            .order_by(Message.created_at)
        )
    ).scalars().all()

    result = await assess_writing(list(rows))

    record = Assessment(
        cefr_level=result.cefr_level,
        ielts_band=result.ielts_band,
        confidence=result.confidence,
        summary_ru=result.summary_ru,
        skills_json=result.skills,
        strengths_json=result.strengths,
        weaknesses_json=result.weaknesses,
        next_steps_json=result.next_steps,
        evidence_json=result.evidence,
        roadmap_json=result.roadmap,
        target_band=result.target_band,
        based_on_messages=result.based_on_messages,
        based_on_words=result.based_on_words,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    signals = await _activity_signals(db)
    return LevelOut(assessment=_to_out(record), **signals)
