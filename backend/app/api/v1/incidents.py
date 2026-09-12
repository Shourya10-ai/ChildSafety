import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentOut
from app.services import incident_service

router = APIRouter()

@router.get("/active", response_model=List[IncidentOut])
async def get_active_incidents(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Returns the most recent safety incidents and alert events for dashboard & alerts feeds."""
    return await incident_service.list_active_incidents(db, limit=limit)

@router.get("/{id}", response_model=IncidentOut)
async def get_incident(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    incident = await incident_service.get_incident_by_id(db, id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident

@router.post("/", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await incident_service.create_incident(db, data)

@router.put("/{id}/verify", response_model=IncidentOut)
async def verify_incident(
    id: uuid.UUID,
    trust_level: str = Query("moderator_verified"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "admin", "authority"))
):
    return await incident_service.verify_incident(db, id, current_user.id, trust_level=trust_level)
