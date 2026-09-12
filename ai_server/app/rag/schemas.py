from typing import List, Optional
from pydantic import BaseModel, Field

class StatutoryCitation(BaseModel):
    statute_name: str = Field(..., description="e.g. POCSO Act 2012, BNS 2023, IT Act 2000")
    section: str = Field(..., description="Specific statutory section or clause")
    relevance_summary: str = Field(..., description="Summary of statutory provision")
    official_source_url: Optional[str] = None

class ModeratorGuidanceQuery(BaseModel):
    incident_type: str
    observed_behavior: str
    victim_age: Optional[int] = None
    suspect_relationship: Optional[str] = None
    query_text: str

class ModeratorGuidanceResponse(BaseModel):
    grounded_guidance: str
    statutory_citations: List[StatutoryCitation]
    mandatory_reporting_required: bool
    reporting_authority: Optional[str] = None  # e.g., "Special Juvenile Police Unit (SJPU) / Child Welfare Committee (CWC)"
    reporting_timeline_hours: Optional[int] = None  # e.g., 24 hours under POCSO Sec 19
    statutory_grounded: bool = True
    confidence_score: float
    disclaimer: str = "Statutory guidance is purely assistive. Human moderators and legal authorities retain final verification responsibility."
