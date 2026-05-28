"""Bridge the markdown vault vocabulary into the DB flashcard deck.

The vault (markdown) is the human-readable knowledge graph; the DB
vocabulary/flashcards tables drive the SRS dashboard. After a session is
saved, we mirror every vault vocabulary note into the deck so new words
become reviewable cards automatically.

Idempotent: matches on word_en, so re-running never duplicates.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import Flashcard
from app.models.vocabulary import Vocabulary
from app.services.vault import Note, list_notes


def _extract_examples(body: str) -> tuple[str | None, str | None]:
    """Pull the first two consecutive blockquote lines as EN / RU example."""
    quotes = [
        line[2:].strip()
        for line in body.splitlines()
        if line.strip().startswith("> ")
    ]
    en = quotes[0] if len(quotes) >= 1 else None
    ru = quotes[1] if len(quotes) >= 2 else None
    return en, ru


def _vocab_fields(note: Note) -> dict:
    fm = note.frontmatter or {}
    word = str(fm.get("word") or note.title).strip()
    example_en, example_ru = _extract_examples(note.body)
    return {
        "word_en": word,
        "lemma_en": (str(fm["lemma"]).strip() if fm.get("lemma") else None),
        "translation_ru": str(fm.get("translation_ru") or "").strip(),
        "part_of_speech": (str(fm["pos"]).strip() if fm.get("pos") else None),
        "cefr_level": (str(fm["cefr"]).strip() if fm.get("cefr") else None),
        "example_en": example_en,
        "example_ru": example_ru,
        "source": f"vault:{note.path}",
    }


async def sync_vault_vocab_to_deck(db: AsyncSession) -> dict[str, int]:
    """Upsert all vault vocabulary notes into vocabulary + flashcards.

    Returns counts: {"vocab_added", "vocab_updated", "cards_added"}.
    """
    notes = list_notes("vocabulary")

    existing_vocab = {
        v.word_en.lower(): v
        for v in (await db.execute(select(Vocabulary))).scalars().all()
    }
    cards_for = {
        fc.vocabulary_id
        for fc in (await db.execute(select(Flashcard))).scalars().all()
    }

    vocab_added = vocab_updated = cards_added = 0
    now = datetime.now(timezone.utc)
    touched: list[Vocabulary] = []

    for note in notes:
        fields = _vocab_fields(note)
        word = fields["word_en"]
        if not word or not fields["translation_ru"]:
            continue
        existing = existing_vocab.get(word.lower())
        if existing is None:
            v = Vocabulary(**fields)
            db.add(v)
            existing_vocab[word.lower()] = v
            touched.append(v)
            vocab_added += 1
        else:
            # Backfill any missing fields without clobbering user edits.
            changed = False
            for key in ("translation_ru", "example_en", "example_ru", "part_of_speech", "cefr_level", "lemma_en"):
                if not getattr(existing, key) and fields.get(key):
                    setattr(existing, key, fields[key])
                    changed = True
            if changed:
                vocab_updated += 1
            touched.append(existing)

    # Flush so freshly-added vocab gets ids before we attach flashcards.
    await db.flush()

    for v in touched:
        if v.id not in cards_for:
            db.add(Flashcard(vocabulary_id=v.id, due_date=now))
            cards_for.add(v.id)
            cards_added += 1

    await db.commit()
    return {
        "vocab_added": vocab_added,
        "vocab_updated": vocab_updated,
        "cards_added": cards_added,
    }
