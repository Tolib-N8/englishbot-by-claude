from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.flashcard import Flashcard
from app.models.message import Message
from app.models.vocabulary import Vocabulary
from app.schemas.flashcard import FlashcardOut
from app.schemas.vocab import (
    VocabExtractResult,
    VocabularyCreate,
    VocabularyOut,
)
from app.services.vocab_extractor import extract_vocabulary

router = APIRouter()


def _to_out(v: Vocabulary, has_flashcard: bool) -> VocabularyOut:
    return VocabularyOut(
        id=v.id,
        word_en=v.word_en,
        lemma_en=v.lemma_en,
        translation_ru=v.translation_ru,
        example_en=v.example_en,
        example_ru=v.example_ru,
        part_of_speech=v.part_of_speech,
        cefr_level=v.cefr_level,
        source=v.source,
        notes=v.notes,
        created_at=v.created_at,
        has_flashcard=has_flashcard,
    )


@router.get("", response_model=list[VocabularyOut])
async def list_vocab(
    q: str | None = Query(None),
    source: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Vocabulary).order_by(Vocabulary.created_at.desc())
    if q:
        stmt = stmt.where(Vocabulary.word_en.ilike(f"%{q}%"))
    if source:
        stmt = stmt.where(Vocabulary.source == source)
    rows = (await db.execute(stmt)).scalars().all()

    fc_rows = (await db.execute(select(Flashcard.vocabulary_id))).scalars().all()
    fc_set = set(fc_rows)
    return [_to_out(v, v.id in fc_set) for v in rows]


@router.post("", response_model=VocabularyOut, status_code=201)
async def create_vocab(body: VocabularyCreate, db: AsyncSession = Depends(get_db)):
    existing = (
        await db.execute(select(Vocabulary).where(Vocabulary.word_en == body.word_en))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "word already exists")
    v = Vocabulary(**body.model_dump())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return _to_out(v, False)


@router.delete("/{vocab_id}", status_code=204)
async def delete_vocab(vocab_id: int, db: AsyncSession = Depends(get_db)):
    v = (
        await db.execute(select(Vocabulary).where(Vocabulary.id == vocab_id))
    ).scalar_one_or_none()
    if v is None:
        raise HTTPException(404, "not found")
    await db.delete(v)
    await db.commit()


@router.post("/from-chat/{message_id}", response_model=VocabExtractResult)
async def extract_from_chat(message_id: int, db: AsyncSession = Depends(get_db)):
    msg = (
        await db.execute(select(Message).where(Message.id == message_id))
    ).scalar_one_or_none()
    if msg is None:
        raise HTTPException(404, "message not found")

    items = await extract_vocabulary(msg.content)

    existing_words = set(
        (await db.execute(select(Vocabulary.word_en))).scalars().all()
    )

    created: list[VocabularyOut] = []
    skipped: list[str] = []
    source = f"chat:{message_id}"

    for item in items:
        word = (item.get("word_en") or "").strip()
        if not word:
            continue
        if word.lower() in {w.lower() for w in existing_words}:
            skipped.append(word)
            continue
        v = Vocabulary(
            word_en=word,
            lemma_en=item.get("lemma_en"),
            translation_ru=item.get("translation_ru") or "",
            example_en=item.get("example_en"),
            example_ru=item.get("example_ru"),
            part_of_speech=item.get("part_of_speech"),
            cefr_level=item.get("cefr_level"),
            source=source,
        )
        db.add(v)
        existing_words.add(word)
        created.append(v)  # type: ignore[arg-type]

    await db.commit()
    for v in created:
        await db.refresh(v)  # type: ignore[arg-type]
    return VocabExtractResult(
        created=[_to_out(v, False) for v in created],  # type: ignore[arg-type]
        skipped_existing=skipped,
    )


@router.post("/{vocab_id}/add-to-deck", response_model=FlashcardOut, status_code=201)
async def add_to_deck(vocab_id: int, db: AsyncSession = Depends(get_db)):
    v = (
        await db.execute(select(Vocabulary).where(Vocabulary.id == vocab_id))
    ).scalar_one_or_none()
    if v is None:
        raise HTTPException(404, "vocab not found")

    existing = (
        await db.execute(select(Flashcard).where(Flashcard.vocabulary_id == vocab_id))
    ).scalar_one_or_none()
    if existing:
        return existing

    fc = Flashcard(vocabulary_id=vocab_id, due_date=datetime.now(timezone.utc))
    db.add(fc)
    await db.commit()
    await db.refresh(fc)
    return fc
