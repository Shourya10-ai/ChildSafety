from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class TranscriptionResponse(BaseModel):
    audio_filename: str
    duration_seconds: float
    transcript: str
    detected_language: str = "en"
    detected_safety_keywords: List[str] = []
    detected_threat_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score: float = 0.95

class VoiceReportResponse(BaseModel):
    report_id: uuid.UUID
    case_id: Optional[uuid.UUID] = None
    protected_case_id: Optional[str] = None
    transcript: str
    category: str
    severity: str
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
