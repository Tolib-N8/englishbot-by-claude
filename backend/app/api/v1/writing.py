"""IELTS Writing endpoints — generate prompts, submit essays, get graded."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_or_create_singleton_user
from app.models.writing import WritingSubmission
from app.schemas.writing import (
    WritingListItem,
    WritingPromptOut,
    WritingPromptRequest,
    WritingResult,
    WritingSubmitRequest,
)
from app.services.writing import (
    ALLOWED_TASKS,
    count_words,
    generate_writing_prompt,
    grade_essay,
)

router = APIRouter()


def _to_result(s: WritingSubmission) -> WritingResult:
    return WritingResult(
        id=s.id,
        task_type=s.task_type,
        prompt_en=s.prompt_en,
        prompt_ru=s.prompt_ru,
        min_words=s.min_words,
        user_text=s.user_text,
        word_count=s.word_count,
        overall_band=s.overall_band,
        criteria=s.criteria_json or [],
        corrections=s.corrections_json or [],
        tip_ru=s.tip_ru,
        created_at=s.created_at,
    )


@router.post("/prompt", response_model=WritingPromptOut)
async def prompt(body: WritingPromptRequest, db: AsyncSession = Depends(get_db)):
    if body.task_type not in ALLOWED_TASKS:
        raise HTTPException(400, "invalid task_type")
    user = await get_or_create_singleton_user(db)
    p = await generate_writing_prompt(body.task_type, user.level)
    return WritingPromptOut(
        task_type=body.task_type,
        prompt_en=p.prompt_en,
        prompt_ru=p.prompt_ru,
        min_words=p.min_words,
    )


@router.post("/submit", response_model=WritingResult)
async def submit(body: WritingSubmitRequest, db: AsyncSession = Depends(get_db)):
    if body.task_type not in ALLOWED_TASKS:
        raise HTTPException(400, "invalid task_type")
    text = body.user_text.strip()
    if not text:
        raise HTTPException(400, "user_text is empty")

    wc = count_words(text)
    grade = await grade_essay(body.task_type, body.prompt_en, text, body.min_words)

    row = WritingSubmission(
        task_type=body.task_type,
        prompt_en=body.prompt_en,
        prompt_ru=body.prompt_ru,
        min_words=body.min_words,
        user_text=text,
        word_count=wc,
        overall_band=grade.overall_band,
        criteria_json=grade.criteria,
        corrections_json=grade.corrections,
        tip_ru=grade.tip_ru,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_result(row)


@router.get("", response_model=list[WritingListItem])
async def list_submissions(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(WritingSubmission)
            .order_by(WritingSubmission.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        WritingListItem(
            id=r.id,
            task_type=r.task_type,
            word_count=r.word_count,
            overall_band=r.overall_band,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{submission_id}", response_model=WritingResult)
async def get_submission(submission_id: int, db: AsyncSession = Depends(get_db)):
    row = (
        await db.execute(select(WritingSubmission).where(WritingSubmission.id == submission_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "not found")
    return _to_result(row)
