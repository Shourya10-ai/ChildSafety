import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.api.v1.reports import get_optional_current_user
from app.models.user import User
from app.schemas.sos import SOSTriggerRequest, SOSResolveRequest, SOSEventOut
from app.services import sos_service

router = APIRouter()

@router.post("/trigger", response_model=SOSEventOut, status_code=status.HTTP_201_CREATED)
async def trigger_emergency_sos(
    data: SOSTriggerRequest,
    db: AsyncSession = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Triggers an emergency SOS event.
    Captures GPS coordinates, creates/attaches to a critical case,
    and executes the emergency notification chain to all linked guardians and assigned moderator.
    """
    user_id = optional_user.id if optional_user else None
    return await sos_service.trigger_sos(db, data, user_id=user_id)

@router.put("/{id}/resolve", response_model=SOSEventOut)
async def resolve_emergency_sos(
    id: uuid.UUID,
    data: SOSResolveRequest = SOSResolveRequest(),
    db: AsyncSession = Depends(get_db),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Resolves an active emergency SOS event.
    """
    user_id = optional_user.id if optional_user else None
    return await sos_service.resolve_sos(db, id, resolver_user_id=user_id, message=data.message)

@router.get("/active", response_model=List[SOSEventOut])
async def get_active_sos(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists currently active emergency SOS events.
    Used by Adult dashboard and emergency response centers.
    """
    return await sos_service.get_active_sos_events(db, limit=limit)

@router.get("/nearby", response_model=List[SOSEventOut])
async def get_nearby_sos(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    radius_km: float = Query(10.0, ge=0.1, le=100.0),
    db: AsyncSession = Depends(get_db)
):
    """
    Spatial proximity query returning active SOS events within radius_km.
    """
    return await sos_service.get_nearby_sos_events(db, latitude, longitude, radius_km=radius_km)

@router.get("/{id}", response_model=SOSEventOut)
async def get_sos_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    event = await sos_service.get_sos_by_id(db, id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS Event not found")
    return event
