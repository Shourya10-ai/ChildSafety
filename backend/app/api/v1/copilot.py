from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_roles, get_current_user
from app.models.user import User
from app.schemas.copilot import (
    CaseSummaryResponse,
    StatutoryQueryRequest,
    StatutoryQueryResponse,
    ChildSafetyChatRequest,
    ChildSafetyChatResponse
)
from app.services.llm_copilot_service import LLMCopilotService
from app.services.statutory_rag_service import StatutoryRAGService

router = APIRouter()

@router.post(
    "/summarize-case/{case_id}",
    response_model=CaseSummaryResponse,
    summary="Generate forensic legal case summary and action plan"
)
async def summarize_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "authority", "admin"))
):
    """
    Synthesizes full case history, incidents, suspect links, evidence chain of custody,
    and predictive risk factors into an executive briefing with applicable statutory
    citations and recommended intervention action plan.
    """
    try:
        return await LLMCopilotService.summarize_case(db, case_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate case summary: {str(e)}")

@router.post(
    "/statutory-query",
    response_model=StatutoryQueryResponse,
    summary="Query Indian child protection legal corpus via RAG"
)
async def query_statutory_corpus(
    query: StatutoryQueryRequest,
    current_user: User = Depends(require_roles("moderator", "authority", "admin"))
):
    """
    Zero-hallucination statutory legal retrieval assistant for safety moderators.
    Searches POCSO Act 2012, BNS 2023, IT Act 2000, JJ Act 2015, and DPDP Act 2023.
    """
    return StatutoryRAGService.generate_grounded_guidance(query)

@router.post(
    "/child-safety-chat",
    response_model=ChildSafetyChatResponse,
    summary="24/7 AI Safety Guardian conversational assistant for children"
)
async def chat_with_safety_guardian(
    request: ChildSafetyChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Safe, empathetic 24/7 conversational assistant for children facing online
    harassment, grooming, or distress. Equipped with emergency keyword interceptors
    and 1-tap SOS escalations.
    """
    return await LLMCopilotService.chat_with_child(db, request)
