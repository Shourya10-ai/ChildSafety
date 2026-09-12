import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.notification import NotificationOut, NotificationList
from app.services import notification_service

router = APIRouter()

@router.get("/", response_model=NotificationList)
async def get_my_notifications(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves incoming notifications (SOS alerts, safety updates) for the logged-in user.
    """
    return await notification_service.get_user_notifications(db, current_user.id, limit=limit)

@router.put("/{id}/read", response_model=dict)
async def mark_as_read(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    success = await notification_service.mark_notification_read(db, id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"status": "success", "message": "Notification marked as read"}
