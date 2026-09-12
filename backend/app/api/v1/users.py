from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User

# Add user schemas if they don't exist yet, we'll assume they do or use a basic pydantic model
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class UserUpdate(BaseModel):
    # Depending on what needs to be updated
    pass

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserOut)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    return current_user

@router.put("/me", response_model=UserOut)
async def update_current_user_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Implementation depends on UserUpdate schema which is omitted,
    # returning current_user for now
    return current_user

@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_roles(["moderator", "authority", "admin"]))])
async def get_user_by_id(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
