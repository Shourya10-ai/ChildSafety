import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.chat import ChatMessageCreate, ChatMessageOut, ChatHistoryResponse
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat & Live Messaging"])

@router.get("/my-case/messages", response_model=ChatHistoryResponse)
async def get_my_active_chat(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Child-friendly endpoint: Returns chat history with assigned protector
    for the current logged-in child without needing case_id upfront.
    """
    if current_user.role != "child":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint only accessible for child accounts. Use /chat/cases/{case_id}/messages for staff."
        )
    return await chat_service.get_child_active_chat(db, current_user, limit=limit, offset=offset)

@router.post("/my-case/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
async def send_message_to_my_case(
    data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Child-friendly endpoint: Sends a message to the active case with the child's
    assigned protector. Auto-dispatches real-time WebSocket event to the moderator.
    """
    if current_user.role != "child":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Endpoint only accessible for child accounts. Use /chat/cases/{case_id}/messages for staff."
        )
    # Find child active case
    active_chat = await chat_service.get_child_active_chat(db, current_user)
    return await chat_service.send_chat_message(db, active_chat.case_id, current_user, data)

@router.get("/cases/{case_id}/messages", response_model=ChatHistoryResponse)
async def get_case_messages(
    case_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Fetches chat message history for a specific case (moderator, child, authority)."""
    return await chat_service.get_chat_history(db, case_id, current_user, limit=limit, offset=offset)

@router.post("/cases/{case_id}/messages", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
async def send_case_message(
    case_id: uuid.UUID,
    data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sends a message in a specific case. Auto-dispatches real-time WebSocket event to the other party."""
    return await chat_service.send_chat_message(db, case_id, current_user, data)

@router.put("/cases/{case_id}/read")
async def mark_case_chat_read(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Marks incoming unread messages as read."""
    read_count = await chat_service.mark_messages_read(db, case_id, current_user)
    return {"message": f"Successfully marked {read_count} messages as read", "read_count": read_count}
