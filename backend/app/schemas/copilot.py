from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class StatutoryCitation(BaseModel):
    statute_name: str
    section: str
    title: str
    relevance_summary: str
    mandatory_reporting: bool = False
    reporting_timeline_hours: Optional[int] = None
    reporting_authority: Optional[str] = None

class StatutoryQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=3, description="Legal or procedural query by moderator")
    incident_type: Optional[str] = "other"
    child_state: Optional[str] = None
    child_district: Optional[str] = None

class StatutoryQueryResponse(BaseModel):
    query: str
    grounded_guidance: str
    statutory_citations: List[StatutoryCitation] = []
    mandatory_reporting_required: bool = False
    reporting_authority: Optional[str] = None
    reporting_timeline_hours: Optional[int] = None
    statutory_grounded: bool = True
    confidence_score: float = 0.95

class CaseMilestone(BaseModel):
    timestamp: Optional[str] = None
    event_type: str
    description: str
    severity: Optional[str] = "medium"

class CaseSummaryResponse(BaseModel):
    case_id: uuid.UUID
    protected_case_id: str
    case_title: Optional[str] = None
    case_priority: str
    case_status: str
    child_protected_id: str
    is_domestic_safety_mode: bool = False
    executive_summary: str
    chronological_milestones: List[CaseMilestone] = []
    suspect_profiles: List[Dict[str, Any]] = []
    applicable_statutory_provisions: List[StatutoryCitation] = []
    recommended_action_plan: List[str] = []
    risk_assessment: Dict[str, Any] = {}
    generated_by: str = "ForensicLegalCopilot-v1"
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ChildSafetyChatMessage(BaseModel):
    sender: str  # "child" or "assistant"
    message: str
    timestamp: Optional[str] = None

class ChildSafetyChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[ChildSafetyChatMessage]] = []
    child_id: Optional[uuid.UUID] = None

class ChildSafetyChatResponse(BaseModel):
    reply: str
    detected_threat: bool = False
    distress_level: str = "NONE"  # NONE, MILD, MODERATE, CRITICAL
    is_emergency: bool = False
    suggest_sos: bool = False
    suggest_moderator_transfer: bool = False
    reassurance_note: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
