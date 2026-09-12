import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.schemas.intelligence import (
    ChildSafetyTimelineResponse,
    CrossCasePatternsResponse,
    ModeratorIntelligenceReportResponse
)
from app.services import intelligence_service

router = APIRouter(prefix="/intelligence", tags=["Longitudinal Safety Intelligence"])

@router.get("/child/{child_id}/timeline", response_model=ChildSafetyTimelineResponse)
async def get_child_timeline(
    child_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns complete chronological safety timeline for a child,
    aggregating cases, infractions, emergency SOS events, and community reports.
    """
    return await intelligence_service.get_child_safety_timeline(db, child_id)

@router.get("/child/{child_id}/patterns", response_model=CrossCasePatternsResponse)
async def get_cross_case_patterns(
    child_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Analyzes historical interactions to surface recurring grooming patterns,
    persistent cyberbullying, emergency surges, and statutory triggers.
    """
    return await intelligence_service.detect_cross_case_patterns(db, child_id)

@router.get("/child/{child_id}/report", response_model=ModeratorIntelligenceReportResponse)
async def get_moderator_intelligence_report(
    child_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Synthesizes a structured longitudinal intelligence dossier with risk trajectory
    and legal/statutory compliance actions for child welfare authorities and court monitors.
    """
    return await intelligence_service.generate_moderator_intelligence_report(db, child_id)
