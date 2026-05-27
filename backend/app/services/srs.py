"""SM-2 spaced repetition algorithm.

Pure function — easy to test, easy to swap to FSRS later.
Reference: Piotr Wozniak's SM-2 algorithm.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SrsState:
    ease: float
    interval_days: int
    repetitions: int
    lapses: int


MIN_EASE = 1.3
DEFAULT_EASE = 2.5


def sm2(state: SrsState, quality: int) -> SrsState:
    """Update SRS state after a review.

    quality: 0 = Again (forgot), 3 = Hard, 4 = Good, 5 = Easy.
    On lapse (quality < 3): interval resets to 1 day, repetitions = 0,
    ease keeps its value (lapse counter increments).
    On success: first review = 1 day, second = 6 days, then interval * ease.
    Ease is updated each turn and floored at MIN_EASE.
    """
    if quality < 0 or quality > 5:
        raise ValueError("quality must be 0..5")

    if quality < 3:
        return SrsState(
            ease=state.ease,
            interval_days=1,
            repetitions=0,
            lapses=state.lapses + 1,
        )

    if state.repetitions == 0:
        new_interval = 1
    elif state.repetitions == 1:
        new_interval = 6
    else:
        new_interval = max(1, round(state.interval_days * state.ease))

    new_ease = state.ease + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    new_ease = max(MIN_EASE, new_ease)

    return SrsState(
        ease=new_ease,
        interval_days=new_interval,
        repetitions=state.repetitions + 1,
        lapses=state.lapses,
    )
