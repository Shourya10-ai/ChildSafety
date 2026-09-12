from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class NominateAdultRequest(BaseModel):
    adult_identifier: str = Field(..., description="Email or phone of the nominated trusted adult")
    relationship_label: str = Field(..., description="Custom descriptive label, e.g. 'Aunt Sunita', 'Teacher Ramesh'")
    reason: Optional[str] = Field(default=None, description="Optional reason for nomination")

class ReviewNominationRequest(BaseModel):
    approved: bool = Field(..., description="Whether to approve or reject the trusted adult nomination")
    vetting_notes: Optional[str] = Field(default=None, description="Moderator rationale/background check notes")

class TrustedAdultResponse(BaseModel):
    link_id: uuid.UUID
    adult_id: uuid.UUID
    child_id: uuid.UUID
    adult_name: Optional[str] = None
    adult_email: Optional[str] = None
    adult_phone: Optional[str] = None
    relationship: str
    relationship_label: Optional[str] = None
    is_alternate_trusted_adult: bool
    nomination_status: str
    linked_at: datetime
    vetted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
