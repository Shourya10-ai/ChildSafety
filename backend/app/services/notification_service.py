import uuid
from typing import List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.models.notification import Notification
from app.schemas.notification import NotificationOut, NotificationList

async def get_user_notifications(db: AsyncSession, user_id: uuid.UUID, limit: int = 50) -> NotificationList:
    res = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    items = res.scalars().all()
    unread_count = sum(1 for n in items if not n.is_read)
    return NotificationList(
        items=[NotificationOut.model_validate(n) for n in items],
        unread_count=unread_count
    )

async def mark_notification_read(db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    res = await db.execute(
        select(Notification)
        .where(and_(Notification.id == notification_id, Notification.user_id == user_id))
    )
    notif = res.scalar_one_or_none()
    if notif:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await db.commit()
        return True
    return False

async def mark_all_notifications_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    res = await db.execute(
        select(Notification).where(and_(Notification.user_id == user_id, Notification.is_read == False))
    )
    unreads = res.scalars().all()
    count = len(unreads)
    for n in unreads:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
    if count > 0:
        await db.commit()
    return count
