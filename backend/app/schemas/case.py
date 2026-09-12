import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field

class CaseStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class CasePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CaseCreate(BaseModel):
    child_id: uuid.UUID
    title: Optional[str] = None
    description: Optional[str] = None
    priority: CasePriority = CasePriority.MEDIUM
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None

class CaseUpdate(BaseModel):
    status: Optional[CaseStatus] = None
    priority: Optional[CasePriority] = None
    title: Optional[str] = None
    description: Optional[str] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    moderator_id: Optional[uuid.UUID] = None

class CaseOut(BaseModel):
    id: uuid.UUID
    child_id: uuid.UUID
    moderator_id: Optional[uuid.UUID] = None
    protected_case_id: str
    status: str
    priority: str
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CaseDetailOut(CaseOut):
    incidents: List[dict] = []
    notes: List[dict] = []
    moderator_name: Optional[str] = None
