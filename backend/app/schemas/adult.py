from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class EmergencyContact(BaseModel):
    name: str
    phone: str
    relationship: str
    is_primary: bool = False

class AdultCreate(BaseModel):
    phone: Optional[str] = None
    emergency_contacts: List[EmergencyContact] = []
    address: Optional[str] = None

class AdultUpdate(BaseModel):
    phone: Optional[str] = None
    emergency_contacts: Optional[List[EmergencyContact]] = None
    address: Optional[str] = None

class AdultOut(BaseModel):
    id: UUID
    user_id: UUID
    phone: Optional[str] = None
    emergency_contacts: List[dict]
    address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
