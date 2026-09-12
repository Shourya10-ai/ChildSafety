import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from fastapi import HTTPException, status

from app.models.case import Case
from app.models.child import Child
from app.models.moderator import Moderator
from app.models.user import User
from app.models.notification import ChatMessage
from app.schemas.chat import ChatMessageCreate, ChatMessageOut, ChatHistoryResponse
from app.core.websocket_manager import ws_manager

async def get_or_verify_case_access(db: AsyncSession, case_id: uuid.UUID, user: User) -> Case:
    """Verifies that user is either the child of the case, or an assigned/authorized moderator or admin."""
    res = await db.execute(select(Case).where(Case.id == case_id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if user.role in ["moderator", "authority", "admin"]:
        return case

    if user.role == "child":
        child_res = await db.execute(select(Child).where(Child.user_id == user.id))
        child = child_res.scalar_one_or_none()
        if child and child.id == case.child_id:
            return case

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access chat for this case")

async def send_chat_message(
    db: AsyncSession,
    case_id: uuid.UUID,
    sender: User,
    data: ChatMessageCreate
) -> ChatMessageOut:
    case = await get_or_verify_case_access(db, case_id, sender)

    # Persist message
    msg = ChatMessage(
        case_id=case.id,
        sender_id=sender.id,
        sender_role=sender.role,
        content=data.content,
        message_type=data.message_type,
        media_url=data.media_url,
        is_read=False
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Determine recipient to push real-time WebSocket event
    recipient_user_ids = []
    
    # 1. Child User ID
    child_res = await db.execute(select(Child).where(Child.id == case.child_id))
    child = child_res.scalar_one_or_none()
    if child and child.user_id and child.user_id != sender.id:
        recipient_user_ids.append(str(child.user_id))

    # 2. Moderator User ID
    if case.moderator_id:
        mod_res = await db.execute(select(Moderator).where(Moderator.id == case.moderator_id))
        mod = mod_res.scalar_one_or_none()
        if mod and mod.user_id and mod.user_id != sender.id:
            recipient_user_ids.append(str(mod.user_id))

    # Outgoing payload
    out_payload = {
        "event": "CHAT_MESSAGE",
        "case_id": str(case.id),
        "protected_case_id": case.protected_case_id,
        "message": {
            "id": str(msg.id),
            "sender_id": str(sender.id),
            "sender_name": sender.full_name or sender.role.capitalize(),
            "sender_role": sender.role,
            "content": msg.content,
            "message_type": msg.message_type,
            "media_url": msg.media_url,
            "created_at": msg.created_at.isoformat() if msg.created_at else datetime.utcnow().isoformat()
        }
    }

    # Deliver to recipient(s) directly via WebSocket
    for r_uid in recipient_user_ids:
        await ws_manager.send_personal_message(out_payload, r_uid)

    return ChatMessageOut(
        id=msg.id,
        case_id=msg.case_id,
        sender_id=msg.sender_id,
        sender_role=msg.sender_role,
        sender_name=sender.full_name or sender.role.capitalize(),
        content=msg.content,
        message_type=msg.message_type,
        media_url=msg.media_url,
        is_read=msg.is_read,
        created_at=msg.created_at
    )

async def get_chat_history(
    db: AsyncSession,
    case_id: uuid.UUID,
    user: User,
    limit: int = 50,
    offset: int = 0
) -> ChatHistoryResponse:
    case = await get_or_verify_case_access(db, case_id, user)

    # Fetch messages
    q = (
        select(ChatMessage, User.full_name)
        .outerjoin(User, User.id == ChatMessage.sender_id)
        .where(ChatMessage.case_id == case.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    rows = res.all()

    total_count_res = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.case_id == case.id)
    )
    total_count = total_count_res.scalar() or 0

    # Look up assigned moderator display name
    moderator_name = None
    if case.moderator_id:
        mod_q = select(User.full_name).select_from(Moderator).join(User, User.id == Moderator.user_id).where(Moderator.id == case.moderator_id)
        mod_res = await db.execute(mod_q)
        moderator_name = mod_res.scalar_one_or_none() or "Duty Child Safety Moderator"

    messages = [
        ChatMessageOut(
            id=m.id,
            case_id=m.case_id,
            sender_id=m.sender_id,
            sender_role=m.sender_role,
            sender_name=full_name or m.sender_role.capitalize(),
            content=m.content,
            message_type=m.message_type,
            media_url=m.media_url,
            is_read=m.is_read,
            created_at=m.created_at
        )
        for m, full_name in rows
    ]

    return ChatHistoryResponse(
        case_id=case.id,
        child_id=case.child_id,
        protected_case_id=case.protected_case_id,
        assigned_moderator_name=moderator_name,
        messages=messages,
        total_count=total_count
    )

async def get_child_active_chat(
    db: AsyncSession,
    child_user: User,
    limit: int = 50,
    offset: int = 0
) -> ChatHistoryResponse:
    """Convenience helper: returns active chat for the currently logged-in child."""
    child_res = await db.execute(select(Child).where(Child.user_id == child_user.id))
    child = child_res.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child profile not found for this account")

    # Find child's most recent active case or open a new one
    from app.services.case_service import get_or_create_active_case_for_child
    case = await get_or_create_active_case_for_child(
        db,
        child_id=child.id,
        title="Active Support Session",
        description="Ongoing safety support and messaging with assigned protector."
    )

    return await get_chat_history(db, case.id, child_user, limit=limit, offset=offset)

async def mark_messages_read(
    db: AsyncSession,
    case_id: uuid.UUID,
    user: User
) -> int:
    case = await get_or_verify_case_access(db, case_id, user)
    now = datetime.utcnow()
    # Mark messages not sent by this user as read
    stmt = (
        update(ChatMessage)
        .where(
            and_(
                ChatMessage.case_id == case.id,
                ChatMessage.sender_id != user.id,
                ChatMessage.is_read == False
            )
        )
        .values(is_read=True, read_at=now)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
