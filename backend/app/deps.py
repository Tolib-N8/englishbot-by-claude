from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


async def get_or_create_singleton_user(db: AsyncSession) -> User:
    """Return the single-user row, creating it on first access."""
    result = await db.execute(select(User).order_by(User.id).limit(1))
    user = result.scalar_one_or_none()
    if user is not None:
        return user
    user = User(level=settings.user_level, native_language=settings.user_native_language)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
