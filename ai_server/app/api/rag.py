from __future__ import annotations
from fastapi import APIRouter
from app.rag.schemas import ModeratorGuidanceQuery, ModeratorGuidanceResponse
from app.rag.statutory_rag import StatutoryRAGCopilot

router = APIRouter()

@router.post("/guidance", response_model=ModeratorGuidanceResponse)
async def get_statutory_guidance(query: ModeratorGuidanceQuery):
    """
    Retrieve grounded Indian statutory legal provisions (POCSO, BNS, IT Act)
    and mandatory reporting obligations for an incident under review.
    """
    return StatutoryRAGCopilot.generate_grounded_guidance(query)
