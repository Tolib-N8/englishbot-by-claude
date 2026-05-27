from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.deps import get_or_create_singleton_user
from app.schemas.meta import Settings as SettingsSchema, SettingsUpdate

router = APIRouter()


@router.get("/settings", response_model=SettingsSchema)
async def get_settings(db: AsyncSession = Depends(get_db)):
    user = await get_or_create_singleton_user(db)
    return SettingsSchema(
        level=user.level,
        native_language=user.native_language,
        model=settings.claude_model or "claude-code-default",
    )


@router.patch("/settings", response_model=SettingsSchema)
async def update_settings(body: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    user = await get_or_create_singleton_user(db)
    if body.level:
        user.level = body.level
    await db.commit()
    await db.refresh(user)
    return SettingsSchema(
        level=user.level,
        native_language=user.native_language,
        model=settings.claude_model or "claude-code-default",
    )
