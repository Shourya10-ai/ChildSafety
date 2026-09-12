import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ReportCreate(BaseModel):
    content: str
    category: str = "other"  # cyberbullying, inappropriate_content, stranger_danger, feeling_unsafe
    platform: Optional[str] = None  # WhatsApp, Instagram, Snapchat, School, Other
    is_anonymous: bool = True
    child_id: Optional[uuid.UUID] = None
    evidence_urls: Optional[List[str]] = None

class ReportOut(BaseModel):
    id: uuid.UUID
    incident_id: Optional[uuid.UUID] = None
    case_id: Optional[uuid.UUID] = None
    reporter_id: Optional[uuid.UUID] = None
    reporter_type: str
    content: str
    is_anonymous: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportSubmissionResponse(BaseModel):
    report_id: uuid.UUID
    case_id: Optional[uuid.UUID] = None
    protected_case_id: Optional[str] = None
    status: str
    message: str
