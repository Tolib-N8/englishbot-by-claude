from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.notes import NoteDetail, NoteSummary, SummarizeResponse
from app.services.session_summarizer import summarize_conversation
from app.services.vault import Note, list_notes, read_note_by_path

router = APIRouter()


def _summary(n: Note) -> NoteSummary:
    fm = n.frontmatter or {}
    return NoteSummary(
        path=n.path,
        folder=n.folder,
        name=n.name,
        title=n.title,
        type=fm.get("type"),
        cefr=fm.get("cefr"),
        date=str(fm.get("date")) if fm.get("date") else None,
    )


@router.get("", response_model=list[NoteSummary])
async def list_all(folder: str | None = Query(None)):
    return [_summary(n) for n in list_notes(folder)]


@router.get("/by-path", response_model=NoteDetail)
async def get_note(path: str = Query(..., description="vault-relative .md path")):
    try:
        n = read_note_by_path(path)
    except FileNotFoundError:
        raise HTTPException(404, "note not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    fm = n.frontmatter or {}
    return NoteDetail(
        path=n.path,
        folder=n.folder,
        name=n.name,
        title=n.title,
        type=fm.get("type"),
        cefr=fm.get("cefr"),
        date=str(fm.get("date")) if fm.get("date") else None,
        frontmatter=fm,
        body=n.body,
        links=n.links(),
    )


@router.post("/summarize/{conversation_id}", response_model=SummarizeResponse)
async def summarize(conversation_id: int, db: AsyncSession = Depends(get_db)):
    conv = (
        await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    ).scalar_one_or_none()
    if conv is None:
        raise HTTPException(404, "conversation not found")

    msgs = (
        await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
    ).scalars().all()
    if not msgs:
        raise HTTPException(400, "conversation has no messages")

    result = await summarize_conversation(conversation_id, list(msgs))
    return SummarizeResponse(
        confirmation=f"Сохранено {len(result.new_note_paths)} заметок"
        + (f" (пропущено {len(result.skipped_paths)})" if result.skipped_paths else "")
        + ".",
        new_note_paths=result.new_note_paths,
    )
