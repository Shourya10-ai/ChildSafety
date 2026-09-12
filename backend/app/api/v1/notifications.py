import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.notification import NotificationList
from app.services import notification_service

router = APIRouter(tags=["Notifications"])

@router.get("/", response_model=NotificationList)
async def get_my_notifications(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns user notification stream with unread tally.
    """
    return await notification_service.get_user_notifications(db, current_user.id, limit=limit)

@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Marks a single notification as read.
    """
    success = await notification_service.mark_notification_read(db, notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"message": "Notification marked as read", "notification_id": notification_id}

@router.put("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Marks all notifications for the current user as read.
    """
    count = await notification_service.mark_all_notifications_read(db, current_user.id)
    return {"message": f"Successfully marked {count} notifications as read", "updated_count": count}
