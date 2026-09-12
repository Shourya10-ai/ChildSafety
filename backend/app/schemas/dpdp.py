import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class DpdpRightsResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    role: str
    is_adult_self_custody: bool
    active_consent_on_file: bool
    consent_status: Optional[str] = None
    eligible_for_erasure: bool
    forensic_retention_locked: bool
    retention_statute: str
    dpdp_statutory_rights: List[str]

class ErasureRequestCreate(BaseModel):
    reason: str
    scope: str = "ALL_NON_STATUTORY_DATA"

class ErasureRequestOut(BaseModel):
    request_id: str
    user_id: uuid.UUID
    status: str
    submitted_at: datetime
    statutory_notes: str

class AgeOfMajorityTransitionResult(BaseModel):
    total_evaluated: int
    transitions_executed: int
    transitioned_child_ids: List[str]
    severs_executed: int
    timestamp: datetime

class DataRetentionSweepResult(BaseModel):
    operational_logs_purged: int
    forensic_records_preserved: int
    timestamp: datetime
