from __future__ import annotations
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker
from app.core.config import settings
from app.models.user import User
import redis.asyncio as redis

bearerscheme = HTTPBearer()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    client = redis.from_url(settings.REDIS_URL)
    try:
        yield client
    finally:
        await client.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearerscheme),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> User:
    from app.services.auth_service import AuthService
    auth_service = AuthService(db, redis_client)
    return await auth_service.get_current_user_from_token(credentials.credentials)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_roles(*roles):
    """Dependency factory: require user to have one of the specified roles."""
    # Flatten in case a list is passed as single argument
    flat_roles = []
    for r in roles:
        if isinstance(r, (list, tuple, set)):
            flat_roles.extend(r)
        else:
            flat_roles.append(r)
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in flat_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(flat_roles)}"
            )
        return current_user
    return role_checker
