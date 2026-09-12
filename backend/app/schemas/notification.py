import uuid
from datetime import datetime
from typing import Optional, Any, Union, Dict, List
from pydantic import BaseModel

class NotificationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    title: str
    body: str
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationList(BaseModel):
    items: List[NotificationOut]
    unread_count: int
