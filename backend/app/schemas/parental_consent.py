import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class ParentalConsentCreate(BaseModel):
    child_id: uuid.UUID
    consent_type: str = "CHILD_ACCOUNT_CREATION"
    verification_method: str = "AFFIRMATION_CHECK"
    statutory_notice_accepted: bool = True
    consent_version: str = "v1.0"

class ParentalConsentOut(BaseModel):
    id: uuid.UUID
    parent_user_id: uuid.UUID
    child_id: uuid.UUID
    consent_type: str
    consent_status: str
    consent_version: str
    verification_method: str
    statutory_notice_accepted: bool
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ConsentVerificationResponse(BaseModel):
    child_id: uuid.UUID
    has_valid_consent: bool
    consent_type: Optional[str] = None
    verified_at: Optional[datetime] = None
    compliance_standard: str = "Digital Personal Data Protection (DPDP) Act, 2023 - Section 9"
