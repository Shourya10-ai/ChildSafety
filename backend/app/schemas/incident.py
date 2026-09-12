import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field

class IncidentType(str, Enum):
    CYBERBULLYING = "cyberbullying"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    STRANGER_DANGER = "stranger_danger"
    FEELING_UNSAFE = "feeling_unsafe"
    GROOMING_RISK = "grooming_risk"
    PHYSICAL_THREAT = "physical_threat"
    OTHER = "other"

class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TrustLevel(str, Enum):
    UNVERIFIED = "unverified"
    AI_FLAGGED = "ai_flagged"
    MODERATOR_VERIFIED = "moderator_verified"
    AUTHORITY_CONFIRMED = "authority_confirmed"

class IncidentCreate(BaseModel):
    case_id: Optional[uuid.UUID] = None
    child_id: Optional[uuid.UUID] = None
    incident_type: IncidentType
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    description: Optional[str] = None
    ai_flags: Optional[Union[Dict[str, Any], List[Any]]] = None
    trust_level: TrustLevel = TrustLevel.UNVERIFIED
    source: str = "child_report"
    occurred_at: Optional[datetime] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

class IncidentUpdate(BaseModel):
    incident_type: Optional[IncidentType] = None
    severity: Optional[IncidentSeverity] = None
    description: Optional[str] = None
    trust_level: Optional[TrustLevel] = None
    is_verified: Optional[bool] = None
    ai_flags: Optional[Union[Dict[str, Any], List[Any]]] = None

class IncidentOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    incident_type: str
    severity: str
    description: Optional[str] = None
    ai_flags: Optional[Union[Dict[str, Any], List[Any]]] = None
    trust_level: str
    source: str
    occurred_at: Optional[datetime] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    is_verified: bool
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
