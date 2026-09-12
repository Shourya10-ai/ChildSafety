import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class SOSTriggerRequest(BaseModel):
    child_id: Optional[uuid.UUID] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    accuracy: Optional[float] = None
    location_address: Optional[str] = None
    message: Optional[str] = None
    is_silent_duress: bool = False
    bypass_primary_guardians: bool = False

class SOSResolveRequest(BaseModel):
    message: Optional[str] = None

class SOSEventOut(BaseModel):
    id: uuid.UUID
    child_id: uuid.UUID
    case_id: Optional[uuid.UUID] = None
    protected_case_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    location_address: Optional[str] = None
    status: str
    message: Optional[str] = None
    child_name: Optional[str] = None
    protected_child_id: Optional[str] = None
    is_silent_duress: bool = False
    routed_to_alternate_adults_only: bool = False
    notified_guardians_count: int = 0
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class SOSProximityQuery(BaseModel):
    latitude: float
    longitude: float
    radius_km: float = 10.0
