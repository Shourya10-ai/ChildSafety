import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class TimelineEventOut(BaseModel):
    event_type: str
    timestamp: datetime
    title: str
    description: Optional[str] = None
    severity: Optional[str] = "medium"
    reference_id: Optional[str] = None
    actor_role: Optional[str] = None

class ChildSafetyTimelineResponse(BaseModel):
    child_id: uuid.UUID
    protected_child_id: str
    display_name: str
    total_events: int
    events: List[TimelineEventOut]

class PatternFlag(BaseModel):
    pattern_type: str
    severity: str
    description: str
    detected_count: int
    first_observed: datetime
    last_observed: datetime
    statutory_relevance: Optional[str] = None

class CrossCasePatternsResponse(BaseModel):
    child_id: uuid.UUID
    total_patterns_detected: int
    highest_risk_level: str
    patterns: List[PatternFlag]

class ModeratorIntelligenceReportResponse(BaseModel):
    child_id: uuid.UUID
    protected_child_id: str
    display_name: str
    age: Optional[int] = None
    total_cases: int
    active_cases: int
    total_sos_events: int
    total_incidents: int
    risk_trajectory: str
    statutory_triggers: List[str] = []
    patterns: List[PatternFlag] = []
    summary_notes: str
    generated_at: datetime
