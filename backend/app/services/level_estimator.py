"""Estimate the learner's CEFR level from accumulated progress.

Signals:
  - vocabulary learned (weighted by the word's own CEFR — harder words count more)
  - whether each word is *mastered* (its flashcard survived a couple of reviews)
    vs merely *seen* (added but not yet retained)
  - grammar topics covered (from the vault, weighted by CEFR)
  - number of saved lesson sessions

The model is a transparent point system → CEFR band. Thresholds are constants
so they're easy to tune. The displayed level never drops below the learner's
self-declared starting level.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import Flashcard
from app.models.vocabulary import Vocabulary
from app.services.vault import list_notes

# Harder words/topics contribute more "knowledge points".
CEFR_VOCAB_WEIGHT = {"A1": 1.0, "A2": 1.5, "B1": 2.5, "B2": 4.0, "C1": 6.0, "C2": 8.0}
CEFR_TOPIC_WEIGHT = {"A1": 2.0, "A2": 3.0, "B1": 5.0, "B2": 8.0, "C1": 12.0, "C2": 16.0}
DEFAULT_VOCAB_WEIGHT = 1.0
DEFAULT_TOPIC_WEIGHT = 2.0

# A flashcard counts as "mastered" once it has survived this many successful reviews.
MASTERY_REPS = 2
# Words that are merely seen (not yet mastered) still count, but less.
UNMASTERED_FACTOR = 0.4
# Each saved lesson adds a little engagement credit.
SESSION_POINTS = 1.5

CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]

# Cumulative point floor required to reach each band.
BAND_FLOORS: list[tuple[str, float]] = [
    ("A1", 0.0),
    ("A2", 40.0),
    ("B1", 120.0),
    ("B2", 280.0),
    ("C1", 600.0),
    ("C2", 1000.0),
]


@dataclass
class LevelEstimate:
    level: str
    declared_level: str
    estimated_level: str
    next_level: str | None
    progress_to_next: int  # 0–100
    points: float
    words_total: int
    words_mastered: int
    topics: int
    sessions: int


def _vocab_weight(cefr: str | None) -> float:
    return CEFR_VOCAB_WEIGHT.get((cefr or "").upper(), DEFAULT_VOCAB_WEIGHT)


def _topic_weight(cefr: str | None) -> float:
    return CEFR_TOPIC_WEIGHT.get((cefr or "").upper(), DEFAULT_TOPIC_WEIGHT)


def _band_for_points(points: float) -> tuple[str, str | None, int]:
    """Return (level, next_level, progress_pct_to_next)."""
    current = BAND_FLOORS[0]
    nxt: tuple[str, float] | None = None
    for i, (name, floor) in enumerate(BAND_FLOORS):
        if points >= floor:
            current = (name, floor)
            nxt = BAND_FLOORS[i + 1] if i + 1 < len(BAND_FLOORS) else None
        else:
            break
    if nxt is None:
        return current[0], None, 100
    span = nxt[1] - current[1]
    progress = int(round((points - current[1]) / span * 100)) if span > 0 else 0
    return current[0], nxt[0], max(0, min(100, progress))


def _higher(a: str, b: str) -> str:
    ia = CEFR_ORDER.index(a) if a in CEFR_ORDER else 0
    ib = CEFR_ORDER.index(b) if b in CEFR_ORDER else 0
    return CEFR_ORDER[max(ia, ib)]


async def estimate_level(db: AsyncSession, declared_level: str) -> LevelEstimate:
    # Vocabulary + mastery (join flashcard repetitions onto each word).
    rows = (
        await db.execute(
            select(Vocabulary.cefr_level, Flashcard.repetitions)
            .join(Flashcard, Flashcard.vocabulary_id == Vocabulary.id, isouter=True)
        )
    ).all()

    words_total = len(rows)
    words_mastered = 0
    vocab_points = 0.0
    for cefr, reps in rows:
        mastered = (reps or 0) >= MASTERY_REPS
        if mastered:
            words_mastered += 1
        factor = 1.0 if mastered else UNMASTERED_FACTOR
        vocab_points += _vocab_weight(cefr) * factor

    # Topics + sessions from the vault.
    topic_notes = list_notes("topics")
    topics = len(topic_notes)
    topic_points = sum(_topic_weight((n.frontmatter or {}).get("cefr")) for n in topic_notes)

    sessions = len(list_notes("sessions"))
    session_points = sessions * SESSION_POINTS

    points = round(vocab_points + topic_points + session_points, 1)
    estimated, next_level, progress = _band_for_points(points)

    declared = declared_level if declared_level in CEFR_ORDER else "A1"
    final_level = _higher(estimated, declared)
    # If we floored up to the declared level, recompute next/progress from there.
    if final_level != estimated:
        idx = CEFR_ORDER.index(final_level)
        next_level = CEFR_ORDER[idx + 1] if idx + 1 < len(CEFR_ORDER) else None
        progress = 0

    return LevelEstimate(
        level=final_level,
        declared_level=declared,
        estimated_level=estimated,
        next_level=next_level,
        progress_to_next=progress,
        points=points,
        words_total=words_total,
        words_mastered=words_mastered,
        topics=topics,
        sessions=sessions,
    )
