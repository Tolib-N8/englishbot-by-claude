import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import AsyncSessionLocal, get_db
from app.deps import get_or_create_singleton_user
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ChatStreamRequest
from app.services.anthropic_client import claude_stream
from app.services.corrections import split_corrections
from app.services.prompts import build_chat_user_message, tutor_system_prompt

router = APIRouter()

HISTORY_LIMIT = 20


def _server_event(event: str, data: dict | str) -> dict:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return {"event": event, "data": payload}


async def _stream(req: ChatStreamRequest) -> AsyncIterator[dict]:
    async with AsyncSessionLocal() as db:
        user = await get_or_create_singleton_user(db)

        result = await db.execute(
            select(Conversation).where(Conversation.id == req.conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            yield _server_event("error", {"detail": "conversation not found"})
            return

        user_msg = Message(conversation_id=conv.id, role="user", content=req.content)
        db.add(user_msg)
        await db.commit()
        await db.refresh(user_msg)
        yield _server_event("user_message_saved", {"id": user_msg.id})

        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .where(Message.id != user_msg.id)
            .order_by(Message.created_at.desc())
            .limit(HISTORY_LIMIT)
        )
        history_rows = list(reversed(history_result.scalars().all()))
        history = [
            {"role": m.role, "content": m.content}
            for m in history_rows
            if m.role in ("user", "assistant")
        ]

        system_prompt = tutor_system_prompt(user.level)
        prompt = build_chat_user_message(history, req.content)

        full_text_parts: list[str] = []

        try:
            async for chunk in claude_stream(
                system_prompt=system_prompt, user_message=prompt
            ):
                full_text_parts.append(chunk)
                yield _server_event("token", {"text": chunk})
        except Exception as exc:
            yield _server_event("error", {"detail": str(exc)})
            return

        raw_text = "".join(full_text_parts)
        clean_text, corrections = split_corrections(raw_text)

        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=clean_text,
            corrections_json=corrections,
        )
        db.add(assistant_msg)
        if conv.title is None:
            conv.title = (req.content[:60] + "…") if len(req.content) > 60 else req.content
        await db.commit()
        await db.refresh(assistant_msg)

        if corrections:
            yield _server_event("corrections", {"items": corrections})
        yield _server_event("done", {"message_id": assistant_msg.id})


@router.post("/stream")
async def chat_stream(req: ChatStreamRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Conversation).where(Conversation.id == req.conversation_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(404, "Conversation not found")
    return EventSourceResponse(_stream(req))
