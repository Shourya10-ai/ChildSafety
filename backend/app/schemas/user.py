from __future__ import annotations
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    language_preference: Optional[str] = None
    fcm_token: Optional[str] = None

class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    role: str
    phone: Optional[str]
    language_preference: str
    is_active: bool
    
    model_config = {"from_attributes": True}
