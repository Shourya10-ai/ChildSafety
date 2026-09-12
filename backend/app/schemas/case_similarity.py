from __future__ import annotations
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

class CaseSimilarityMatch(BaseModel):
    case_id: uuid.UUID
    protected_case_id: str
    title: Optional[str] = None
    status: str
    priority: str
    similarity_score: float = Field(..., description="Normalized composite similarity score 0.0 to 1.0")
    common_modus_operandi: List[str] = Field(default_factory=list)
    shared_suspects: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    spatial_proximity_match: bool = False
    temporal_delta_days: int = 0
    match_reasons: List[str] = Field(default_factory=list)

class CaseSimilarityResponse(BaseModel):
    query_case_id: uuid.UUID
    query_protected_case_id: str
    top_matches: List[CaseSimilarityMatch]
    total_candidates_analyzed: int
