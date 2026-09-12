import uuid
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel

class NoteType(str, Enum):
    OBSERVATION = "observation"
    ACTION_TAKEN = "action_taken"
    COUNSELING_SUMMARY = "counseling_summary"
    ESCALATION_REASON = "escalation_reason"

class ModeratorNoteCreate(BaseModel):
    content: str
    note_type: NoteType = NoteType.OBSERVATION

class ModeratorNoteOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    moderator_id: uuid.UUID
    content: str
    note_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ModeratorOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_id: Optional[str] = None
    specialization: Optional[str] = None
    active_case_count: int
    max_cases: int
    is_available: bool

    class Config:
        from_attributes = True

class EscalationCreate(BaseModel):
    reason: str
    priority: str = "high"
    notes: Optional[str] = None

class EscalationOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    from_moderator_id: uuid.UUID
    to_authority_id: Optional[uuid.UUID] = None
    reason: str
    status: str
    priority: str
    notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
