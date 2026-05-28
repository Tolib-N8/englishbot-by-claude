from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_or_create_singleton_user
from app.models.assessment import Assessment
from app.models.exercise import ExerciseAttempt, GrammarExercise
from app.schemas.exercise import (
    AttemptRequest,
    AttemptResult,
    ExerciseOut,
    ExerciseStats,
    GenerateRequest,
    TopicSuggestion,
)
from app.services.exercise_generator import generate_exercises
from app.services.exercise_grader import grade_attempt

router = APIRouter()

COMMON_TOPICS = [
    "Present Simple vs Present Continuous",
    "Past Simple vs Present Perfect",
    "Articles (a / an / the)",
    "Prepositions of time (in / on / at)",
    "Comparatives and superlatives",
    "Gerunds and infinitives (like + V-ing / to V)",
    "Conditionals (zero / first)",
    "Word order in questions",
]


async def _attempt_index(db: AsyncSession) -> dict[int, bool]:
    """Map exercise_id → last is_correct (only for exercises that were attempted)."""
    rows = (
        await db.execute(
            select(ExerciseAttempt.exercise_id, ExerciseAttempt.is_correct).order_by(
                ExerciseAttempt.created_at
            )
        )
    ).all()
    last: dict[int, bool] = {}
    for ex_id, correct in rows:
        last[ex_id] = bool(correct)
    return last


def _to_out(ex: GrammarExercise, attempt_index: dict[int, bool]) -> ExerciseOut:
    return ExerciseOut(
        id=ex.id,
        topic=ex.topic,
        level=ex.level,
        type=ex.type,
        prompt=ex.prompt,
        prompt_ru=ex.prompt_ru,
        choices_json=ex.choices_json,
        created_at=ex.created_at,
        attempted=ex.id in attempt_index,
        last_correct=attempt_index.get(ex.id),
    )


@router.get("/topics", response_model=list[TopicSuggestion])
async def topics(db: AsyncSession = Depends(get_db)):
    suggestions: list[TopicSuggestion] = []
    seen: set[str] = set()

    latest = (
        await db.execute(select(Assessment).order_by(Assessment.created_at.desc()).limit(1))
    ).scalar_one_or_none()
    if latest and latest.roadmap_json:
        for phase in latest.roadmap_json:
            title = (phase or {}).get("title") if isinstance(phase, dict) else None
            if title:
                # Strip a leading "Этап N: " prefix for a cleaner topic.
                clean = title.split(":", 1)[-1].strip() if ":" in title else title.strip()
                if clean.lower() not in seen:
                    seen.add(clean.lower())
                    suggestions.append(TopicSuggestion(topic=clean, source="roadmap"))

    for t in COMMON_TOPICS:
        if t.lower() not in seen:
            seen.add(t.lower())
            suggestions.append(TopicSuggestion(topic=t, source="common"))
    return suggestions


@router.get("/stats", response_model=ExerciseStats)
async def stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(GrammarExercise.id)))).scalar_one()
    idx = await _attempt_index(db)
    attempted = len(idx)
    correct = sum(1 for v in idx.values() if v)
    accuracy = round(correct / attempted * 100) if attempted else 0
    return ExerciseStats(total=int(total), attempted=attempted, correct=correct, accuracy=accuracy)


@router.post("/generate", response_model=list[ExerciseOut])
async def generate(body: GenerateRequest, db: AsyncSession = Depends(get_db)):
    user = await get_or_create_singleton_user(db)
    items = await generate_exercises(
        topic=body.topic, level=user.level, count=body.count, types=body.types
    )
    if not items:
        raise HTTPException(502, "Не удалось сгенерировать упражнения, попробуй ещё раз")

    created: list[GrammarExercise] = []
    for it in items:
        ex = GrammarExercise(
            topic=body.topic,
            level=user.level,
            type=it["type"],
            prompt=it["prompt"],
            prompt_ru=it["prompt_ru"],
            answer=it["answer"],
            alternatives_json=it["alternatives"],
            choices_json=it["choices"],
            explanation_ru=it["explanation_ru"],
            source="manual",
        )
        db.add(ex)
        created.append(ex)
    await db.commit()
    for ex in created:
        await db.refresh(ex)
    return [_to_out(ex, {}) for ex in created]


@router.get("", response_model=list[ExerciseOut])
async def list_exercises(
    status: str = Query("all", pattern="^(all|pending|done)$"),
    topic: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    idx = await _attempt_index(db)
    stmt = select(GrammarExercise).order_by(GrammarExercise.created_at.desc())
    if topic:
        stmt = stmt.where(GrammarExercise.topic == topic)
    rows = (await db.execute(stmt)).scalars().all()
    out = [_to_out(ex, idx) for ex in rows]
    if status == "pending":
        out = [e for e in out if not e.attempted]
    elif status == "done":
        out = [e for e in out if e.attempted]
    return out


@router.get("/{exercise_id}", response_model=ExerciseOut)
async def get_exercise(exercise_id: int, db: AsyncSession = Depends(get_db)):
    ex = (
        await db.execute(select(GrammarExercise).where(GrammarExercise.id == exercise_id))
    ).scalar_one_or_none()
    if ex is None:
        raise HTTPException(404, "not found")
    idx = await _attempt_index(db)
    return _to_out(ex, idx)


@router.post("/{exercise_id}/attempt", response_model=AttemptResult)
async def attempt(exercise_id: int, body: AttemptRequest, db: AsyncSession = Depends(get_db)):
    ex = (
        await db.execute(select(GrammarExercise).where(GrammarExercise.id == exercise_id))
    ).scalar_one_or_none()
    if ex is None:
        raise HTTPException(404, "not found")

    result = await grade_attempt(ex, body.user_answer)
    db.add(
        ExerciseAttempt(
            exercise_id=ex.id,
            user_answer=body.user_answer,
            is_correct=result.is_correct,
            feedback_ru=result.feedback_ru,
        )
    )
    await db.commit()
    return AttemptResult(
        is_correct=result.is_correct,
        feedback_ru=result.feedback_ru,
        answer=ex.answer,
        explanation_ru=ex.explanation_ru,
    )
