from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.flashcard import Flashcard
from app.schemas.flashcard import (
    FlashcardOut,
    FlashcardStats,
    FlashcardWithVocab,
    ReviewRequest,
)
from app.services.srs import SrsState, sm2
from app.services.vault_sync import sync_vault_vocab_to_deck

router = APIRouter()


@router.post("/sync-vault")
async def sync_vault(db: AsyncSession = Depends(get_db)):
    """Mirror every vault vocabulary note into the deck (idempotent)."""
    return await sync_vault_vocab_to_deck(db)


def _with_vocab(fc: Flashcard) -> FlashcardWithVocab:
    v = fc.vocabulary
    return FlashcardWithVocab(
        id=fc.id,
        vocabulary_id=fc.vocabulary_id,
        ease=fc.ease,
        interval_days=fc.interval_days,
        repetitions=fc.repetitions,
        due_date=fc.due_date,
        last_reviewed_at=fc.last_reviewed_at,
        lapses=fc.lapses,
        suspended=fc.suspended,
        word_en=v.word_en,
        translation_ru=v.translation_ru,
        example_en=v.example_en,
        example_ru=v.example_ru,
        part_of_speech=v.part_of_speech,
    )


@router.get("/due", response_model=list[FlashcardWithVocab])
async def due_cards(
    limit: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    stmt = (
        select(Flashcard)
        .options(selectinload(Flashcard.vocabulary))
        .where(Flashcard.suspended.is_(False))
        .where(Flashcard.due_date <= now)
        .order_by(Flashcard.due_date)
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_with_vocab(fc) for fc in rows]


@router.get("/stats", response_model=FlashcardStats)
async def flashcard_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = (await db.execute(select(func.count(Flashcard.id)))).scalar_one()
    due_now = (
        await db.execute(
            select(func.count(Flashcard.id))
            .where(Flashcard.suspended.is_(False))
            .where(Flashcard.due_date <= now)
        )
    ).scalar_one()
    reviewed_today = (
        await db.execute(
            select(func.count(Flashcard.id)).where(Flashcard.last_reviewed_at >= today_start)
        )
    ).scalar_one()
    new_today = (
        await db.execute(
            select(func.count(Flashcard.id)).where(Flashcard.repetitions == 0)
        )
    ).scalar_one()
    return FlashcardStats(
        total=int(total),
        due_now=int(due_now),
        reviewed_today=int(reviewed_today),
        new_today=int(new_today),
    )


@router.post("/{card_id}/review", response_model=FlashcardOut)
async def review_card(
    card_id: int, body: ReviewRequest, db: AsyncSession = Depends(get_db)
):
    fc = (
        await db.execute(select(Flashcard).where(Flashcard.id == card_id))
    ).scalar_one_or_none()
    if fc is None:
        raise HTTPException(404, "card not found")

    state = SrsState(
        ease=fc.ease,
        interval_days=fc.interval_days,
        repetitions=fc.repetitions,
        lapses=fc.lapses,
    )
    new_state = sm2(state, body.quality)

    now = datetime.now(timezone.utc)
    fc.ease = new_state.ease
    fc.interval_days = new_state.interval_days
    fc.repetitions = new_state.repetitions
    fc.lapses = new_state.lapses
    fc.last_reviewed_at = now
    fc.due_date = now + timedelta(days=max(1, new_state.interval_days))
    await db.commit()
    await db.refresh(fc)
    return fc
