import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class MissingChildCreate(BaseModel):
    child_name: str
    photo_url: str
    description: str
    age_when_missing: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    clothing_description: Optional[str] = None
    identifying_marks: Optional[str] = None
    last_known_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    child_id: Optional[uuid.UUID] = None

class SightingCreate(BaseModel):
    image_url: Optional[str] = None
    location_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sighting_notes: Optional[str] = None
    captured_at: Optional[datetime] = None

class SightingOut(BaseModel):
    id: uuid.UUID
    missing_child_id: uuid.UUID
    image_url: Optional[str] = None
    similarity_score: Optional[float] = 0.0
    location_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    captured_at: Optional[datetime] = None
    source: str
    sighting_notes: Optional[str] = None
    status: str
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MissingChildOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    child_id: Optional[uuid.UUID] = None
    child_name: str
    photo_url: str
    description: str
    age_when_missing: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    clothing_description: Optional[str] = None
    identifying_marks: Optional[str] = None
    last_known_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MissingChildDetailOut(MissingChildOut):
    protected_case_id: Optional[str] = None
    sightings: List[SightingOut] = []

class VerifySightingRequest(BaseModel):
    is_match: bool
    notes: Optional[str] = None

class ResolveMissingChildRequest(BaseModel):
    resolution_notes: str
