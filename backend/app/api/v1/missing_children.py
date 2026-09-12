import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.schemas.missing_child import (
    MissingChildCreate, MissingChildOut, MissingChildDetailOut,
    SightingCreate, SightingOut, VerifySightingRequest, ResolveMissingChildRequest
)
from app.services import missing_child_service

router = APIRouter(prefix="/missing-children", tags=["Missing Children & Sightings"])

@router.post("/", response_model=MissingChildOut, status_code=status.HTTP_201_CREATED)
async def report_missing_child(
    data: MissingChildCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Files an emergency missing child report.
    Automatically generates a linked critical case, assigns a local safety protector,
    and broadcasts an emergency alert to all responders.
    """
    return await missing_child_service.report_missing_child(db, data, current_user)

@router.get("/", response_model=List[MissingChildOut])
async def list_active_missing_children(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Lists active missing children alerts, optionally filtered by state/district."""
    return await missing_child_service.list_active_missing_children(db, limit, offset, state, district)

@router.get("/{missing_child_id}", response_model=MissingChildDetailOut)
async def get_missing_child_detail(
    missing_child_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Fetches full missing child profile including citizen sighting reports timeline."""
    return await missing_child_service.get_missing_child_detail(db, missing_child_id)

@router.post("/{missing_child_id}/sightings", response_model=SightingOut, status_code=status.HTTP_201_CREATED)
async def submit_sighting(
    missing_child_id: uuid.UUID,
    data: SightingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submits a geo-tagged citizen sighting with photo evidence for human moderator verification."""
    return await missing_child_service.submit_sighting(db, missing_child_id, data, current_user)

@router.put("/sightings/{sighting_id}/verify", response_model=SightingOut)
async def verify_sighting(
    sighting_id: uuid.UUID,
    data: VerifySightingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """Human moderator verification of candidate image sighting."""
    return await missing_child_service.verify_sighting(db, sighting_id, current_user, data.is_match, data.notes)

@router.put("/{missing_child_id}/resolve", response_model=MissingChildOut)
async def resolve_missing_child_case(
    missing_child_id: uuid.UUID,
    data: ResolveMissingChildRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """Marks a missing child as located / safe and closes the linked emergency case."""
    return await missing_child_service.resolve_missing_child(db, missing_child_id, current_user, data.resolution_notes)
