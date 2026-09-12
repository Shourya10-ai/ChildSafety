import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class ChatMessageCreate(BaseModel):
    content: str
    message_type: str = "text"
    media_url: Optional[str] = None

class ChatMessageOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    sender_id: uuid.UUID
    sender_role: str
    sender_name: Optional[str] = None
    content: str
    message_type: str
    media_url: Optional[str] = None
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatHistoryResponse(BaseModel):
    case_id: uuid.UUID
    child_id: uuid.UUID
    protected_case_id: Optional[str] = None
    assigned_moderator_name: Optional[str] = None
    messages: List[ChatMessageOut]
    total_count: int
