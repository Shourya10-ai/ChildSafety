from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PolicyEvaluationRequest(BaseModel):
    user_id: str
    role: str
    user_state: Optional[str] = None
    user_district: Optional[str] = None
    elevated_jurisdiction: bool = False
    linked_child_ids: List[str] = []
    resource_type: str  # case, incident, report, identity_vault, chat, sos
    resource_id: str
    resource_child_id: Optional[str] = None
    resource_state: Optional[str] = None
    resource_district: Optional[str] = None
    assigned_moderator_id: Optional[str] = None
    is_domestic_safety_mode: bool = False
    is_solo_setup: bool = False
    is_active_sos: bool = False
    action: str  # read, write, update, delete, assign, resolve_vault, emergency_override
    justification: Optional[str] = None
    is_emergency: bool = False


class PolicyDecisionResponse(BaseModel):
    allowed: bool
    policy_rule: str
    reason: str
    subject_role: str
    resource_type: str
    action: str


class AuditLogEntrySchema(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    prev_hash: Optional[str] = None
    entry_hash: Optional[str] = None
    signature: Optional[str] = None
    bsa_section: Optional[str] = None
    timestamp: datetime


class AuditChainVerificationResponse(BaseModel):
    is_valid: bool
    total_records_verified: int
    head_hash: Optional[str] = None
    tampered_record_id: Optional[str] = None
    failure_reason: Optional[str] = None
    certificate: Optional[str] = None
    verified_at: str


class VaultResolutionRequest(BaseModel):
    protected_child_id: str
    authorized_reason: str = Field(..., min_length=10, description="Mandatory legal justification / FIR / CWC warrant")
    fir_number: Optional[str] = None


class VaultResolutionResponse(BaseModel):
    protected_child_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    school: Optional[str] = None
    guardian_info: Optional[str] = None
    audit_log_id: str
    entry_hash: str
    bsa_compliance: str


class MaskedIdentityResponse(BaseModel):
    protected_child_id: str
    is_registered: bool
    masked_name: Optional[str] = None
    masked_phone: Optional[str] = None
    masked_address: Optional[str] = None
    has_school_record: bool
    has_guardian_record: bool
    encryption_algorithm: str


class EdgeScanSyncRequest(BaseModel):
    child_id: str
    source_type: str = Field(default="TEXT", description="TEXT or SCREENSHOT_OCR")
    raw_content: Optional[str] = None
    detected_threat_level: str = Field(default="SAFE", description="SAFE, SUSPICIOUS, HIGH_RISK, CRITICAL")
    detected_indicators: List[str] = []
    recommended_action: str = Field(default="NONE", description="NONE, ADVICE_CHIP, SHOW_DECOY_EXIT, EMERGENCY_INTERCEPT")
    timestamp: Optional[datetime] = None


class EdgeScanSyncResponse(BaseModel):
    status: str
    child_id: str
    edge_risk_acknowledged: bool
    server_risk_score: float
    recommended_intervention: str
    audit_chain_hash: Optional[str] = None
