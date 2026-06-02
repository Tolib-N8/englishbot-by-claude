"""IELTS Writing endpoints — generate prompts, submit essays, get graded."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_or_create_singleton_user
from datetime import datetime, timezone

from app.models.writing import WritingSubmission
from app.models.writing_lesson import WritingLesson
from app.schemas.writing import (
    LessonDetail,
    LessonSummary,
    TemplateDetail,
    TemplateSummary,
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
from app.services.writing_lessons import (
    CURRICULUM,
    generate_lesson_body,
    get_lesson_spec,
)
from app.services.writing_templates import (
    TEMPLATES,
    generate_template_body,
    get_template_spec,
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


# --- Lessons (curriculum) — declared BEFORE /{submission_id} so the literal
#     `/lessons` prefix wins over the int-typed catch-all.


@router.get("/lessons", response_model=list[LessonSummary])
async def list_lessons(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(WritingLesson))).scalars().all()
    by_slug = {r.slug: r for r in rows}
    return [
        LessonSummary(
            slug=spec.slug,
            title=spec.title,
            summary=spec.summary,
            order=i + 1,
            read=(by_slug.get(spec.slug) is not None and by_slug[spec.slug].read_at is not None),
            generated=spec.slug in by_slug,
        )
        for i, spec in enumerate(CURRICULUM)
    ]


@router.get("/lessons/{slug}", response_model=LessonDetail)
async def get_lesson(slug: str, db: AsyncSession = Depends(get_db)):
    spec = get_lesson_spec(slug)
    if spec is None:
        raise HTTPException(404, "unknown lesson")

    row = (
        await db.execute(select(WritingLesson).where(WritingLesson.slug == slug))
    ).scalar_one_or_none()
    if row is None:
        body = await generate_lesson_body(spec)
        row = WritingLesson(slug=slug, body_md=body)
        db.add(row)
        await db.commit()
        await db.refresh(row)

    order = next(i for i, s in enumerate(CURRICULUM) if s.slug == slug)
    return LessonDetail(
        slug=spec.slug,
        title=spec.title,
        summary=spec.summary,
        order=order + 1,
        body_md=row.body_md,
        read=row.read_at is not None,
        generated_at=row.generated_at,
        prev_slug=CURRICULUM[order - 1].slug if order > 0 else None,
        next_slug=CURRICULUM[order + 1].slug if order + 1 < len(CURRICULUM) else None,
    )


@router.post("/lessons/{slug}/read", response_model=LessonDetail)
async def mark_lesson_read(slug: str, db: AsyncSession = Depends(get_db)):
    spec = get_lesson_spec(slug)
    if spec is None:
        raise HTTPException(404, "unknown lesson")
    row = (
        await db.execute(select(WritingLesson).where(WritingLesson.slug == slug))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "lesson not generated yet")
    row.read_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    order = next(i for i, s in enumerate(CURRICULUM) if s.slug == slug)
    return LessonDetail(
        slug=spec.slug,
        title=spec.title,
        summary=spec.summary,
        order=order + 1,
        body_md=row.body_md,
        read=row.read_at is not None,
        generated_at=row.generated_at,
        prev_slug=CURRICULUM[order - 1].slug if order > 0 else None,
        next_slug=CURRICULUM[order + 1].slug if order + 1 < len(CURRICULUM) else None,
    )


# --- Templates (Task 2 essay skeletons) -------------------------------------


@router.get("/templates", response_model=list[TemplateSummary])
async def list_templates(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(WritingLesson).where(WritingLesson.slug.like("tmpl-%"))
        )
    ).scalars().all()
    by_slug = {r.slug: r for r in rows}
    return [
        TemplateSummary(
            slug=t.slug,
            title=t.title,
            summary=t.summary,
            order=i + 1,
            generated=t.slug in by_slug,
        )
        for i, t in enumerate(TEMPLATES)
    ]


@router.get("/templates/{slug}", response_model=TemplateDetail)
async def get_template(slug: str, db: AsyncSession = Depends(get_db)):
    spec = get_template_spec(slug)
    if spec is None:
        raise HTTPException(404, "unknown template")

    row = (
        await db.execute(select(WritingLesson).where(WritingLesson.slug == slug))
    ).scalar_one_or_none()
    if row is None:
        body = await generate_template_body(spec)
        row = WritingLesson(slug=slug, body_md=body)
        db.add(row)
        await db.commit()
        await db.refresh(row)

    order = next(i for i, t in enumerate(TEMPLATES) if t.slug == slug)
    return TemplateDetail(
        slug=spec.slug,
        title=spec.title,
        summary=spec.summary,
        order=order + 1,
        body_md=row.body_md,
        generated_at=row.generated_at,
        prev_slug=TEMPLATES[order - 1].slug if order > 0 else None,
        next_slug=TEMPLATES[order + 1].slug if order + 1 < len(TEMPLATES) else None,
    )


# --- Past submission detail (kept last because the path matches anything) ----


@router.get("/{submission_id}", response_model=WritingResult)
async def get_submission(submission_id: int, db: AsyncSession = Depends(get_db)):
    row = (
        await db.execute(select(WritingSubmission).where(WritingSubmission.id == submission_id))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "not found")
    return _to_result(row)
