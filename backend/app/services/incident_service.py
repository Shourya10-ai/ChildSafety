import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from app.models.case import Incident, Case
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.services.case_service import get_or_create_active_case_for_child, get_case_by_id

async def create_incident(db: AsyncSession, data: IncidentCreate) -> Incident:
    case_id = data.case_id
    if not case_id:
        if not data.child_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either case_id or child_id must be provided to create an incident"
            )
        active_case = await get_or_create_active_case_for_child(
            db,
            child_id=data.child_id,
            title=f"Incident: {data.incident_type.value.replace('_', ' ').title()}",
            priority=data.severity.value
        )
        case_id = active_case.id
    else:
        case = await get_case_by_id(db, case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    new_incident = Incident(
        case_id=case_id,
        incident_type=data.incident_type.value,
        severity=data.severity.value,
        description=data.description,
        ai_flags=data.ai_flags,
        trust_level=data.trust_level.value,
        source=data.source,
        occurred_at=data.occurred_at or datetime.now(timezone.utc),
        location_lat=data.location_lat,
        location_lng=data.location_lng,
        is_verified=False
    )
    db.add(new_incident)
    await db.commit()
    await db.refresh(new_incident)
    return new_incident

async def get_incident_by_id(db: AsyncSession, incident_id: uuid.UUID) -> Optional[Incident]:
    res = await db.execute(select(Incident).where(Incident.id == incident_id))
    return res.scalar_one_or_none()

async def list_incidents_for_case(db: AsyncSession, case_id: uuid.UUID) -> List[Incident]:
    res = await db.execute(
        select(Incident)
        .where(Incident.case_id == case_id)
        .order_by(Incident.created_at.desc())
    )
    return list(res.scalars().all())

async def list_active_incidents(db: AsyncSession, limit: int = 50) -> List[Incident]:
    res = await db.execute(
        select(Incident)
        .order_by(Incident.created_at.desc())
        .limit(limit)
    )
    return list(res.scalars().all())

async def verify_incident(
    db: AsyncSession,
    incident_id: uuid.UUID,
    verified_by_user_id: uuid.UUID,
    trust_level: str = "moderator_verified"
) -> Incident:
    incident = await get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    incident.is_verified = True
    incident.verified_by = verified_by_user_id
    incident.verified_at = datetime.now(timezone.utc)
    incident.trust_level = trust_level

    await db.commit()
    await db.refresh(incident)
    return incident
