from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.adult import AdultOut, AdultUpdate
from app.schemas.child import ChildOut
from app.services import adult_service, child_service

router = APIRouter(prefix="/adults", tags=["Adult Management"])

@router.get("/me", response_model=AdultOut)
async def get_my_adult_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    adult = await adult_service.get_or_create_adult(db, current_user.id)
    return adult

@router.put("/me", response_model=AdultOut)
async def update_my_adult_profile(
    data: AdultUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    adult = await adult_service.get_or_create_adult(db, current_user.id)
    return await adult_service.update_adult(db, adult.id, data)

@router.get("/me/children", response_model=List[ChildOut])
async def get_my_linked_children(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    adult = await adult_service.get_or_create_adult(db, current_user.id)
    return await child_service.get_children_for_adult(db, adult.id)
