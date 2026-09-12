from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class RiskFactorBreakdown(BaseModel):
    velocity_score: float = Field(..., description="Threat acceleration & frequency within 24-72 hours (0.0 to 1.0)")
    severity_score: float = Field(..., description="Weighted severity of reported incidents (0.0 to 1.0)")
    predator_persistence_score: float = Field(..., description="Multi-platform contact attempts & coercion indicators (0.0 to 1.0)")
    vulnerability_score: float = Field(..., description="Child age, unmonitored status, domestic danger bypass (0.0 to 1.0)")

class StatutoryCitation(BaseModel):
    act: str = Field(..., description="e.g. POCSO Act 2012, BNS 2023, IT Act 2000")
    section: str = Field(..., description="Statutory section number")
    provision: str = Field(..., description="Legal provision name or offense description")
    mandatory_action: str = Field(..., description="Statutory obligation (e.g. SJPU reporting, CWC referral)")

class RiskEvaluationResponse(BaseModel):
    target_type: str = "CASE"  # CASE or CHILD
    target_id: uuid.UUID
    protected_id: str
    composite_risk_score: float = Field(..., description="Composite normalized risk score 0.0 to 1.0")
    threat_tier: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    factors: RiskFactorBreakdown
    statutory_citations: List[StatutoryCitation] = Field(default_factory=list)
    recommended_interventions: List[str] = Field(default_factory=list)
    evaluated_at: datetime
