from typing import Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

class ChildCreate(BaseModel):
    display_name: str
    age: Optional[int] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    language_preference: str = "en"

class ChildUpdate(BaseModel):
    display_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    language_preference: Optional[str] = None

class ChildOut(BaseModel):
    id: UUID
    protected_child_id: str
    display_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    language_preference: str
    created_by: Optional[UUID] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LinkChildRequest(BaseModel):
    protected_child_id: str
    relationship: str = "parent"

class ChildLinkOut(BaseModel):
    id: UUID
    adult_id: UUID
    child_id: UUID
    relationship: str
    is_primary: bool
    is_verified: bool
    linked_at: datetime
    child: Optional[ChildOut] = None

    model_config = ConfigDict(from_attributes=True)
