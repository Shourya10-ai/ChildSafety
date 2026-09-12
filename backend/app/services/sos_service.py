import uuid
import math
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.sos import SOSEvent
from app.models.case import Case, Incident
from app.models.child import Child, Adult, AdultChildLink
from app.models.user import User
from app.models.moderator import Moderator
from app.models.notification import Notification
from app.schemas.sos import SOSTriggerRequest, SOSResolveRequest, SOSEventOut
from app.services.case_service import get_or_create_active_case_for_child
from app.core.security import generate_protected_child_id

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth's radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

async def trigger_sos(
    db: AsyncSession,
    data: SOSTriggerRequest,
    user_id: Optional[uuid.UUID] = None
) -> SOSEventOut:
    # 1. Resolve Child
    child = None
    if data.child_id:
        res = await db.execute(select(Child).where(Child.id == data.child_id))
        child = res.scalar_one_or_none()
    elif user_id:
        res = await db.execute(select(Child).where(Child.user_id == user_id))
        child = res.scalar_one_or_none()

    if not child:
        # Fallback or create placeholder for SOS sender
        res = await db.execute(select(Child).limit(1))
        child = res.scalar_one_or_none()
        if not child:
            child = Child(
                protected_child_id=generate_protected_child_id(),
                display_name="Child in Need",
                age=12
            )
            db.add(child)
            await db.commit()
            await db.refresh(child)

    # 2. Auto Case Creation (Critical Priority)
    case = await get_or_create_active_case_for_child(
        db,
        child_id=child.id,
        title=f"CRITICAL: Emergency SOS Triggered by {child.display_name}",
        description=f"Emergency SOS triggered at coordinates ({data.latitude:.4f}, {data.longitude:.4f})",
        priority="critical"
    )

    # 3. Create SOSEvent
    location_str = data.location_address or f"GPS ({data.latitude:.4f}, {data.longitude:.4f})"
    sos_event = SOSEvent(
        child_id=child.id,
        case_id=case.id,
        latitude=data.latitude,
        longitude=data.longitude,
        accuracy=data.accuracy,
        location_address=location_str,
        status="active",
        message=data.message or "Emergency assistance requested"
    )
    db.add(sos_event)

    # 4. Create Critical Incident
    incident = Incident(
        case_id=case.id,
        incident_type="physical_threat",
        severity="critical",
        description=f"Emergency SOS triggered by {child.display_name} at {location_str}",
        trust_level="ai_flagged",
        source="sos_button",
        location_lat=data.latitude,
        location_lng=data.longitude,
        is_verified=False
    )
    db.add(incident)

    # 5. Execute Emergency Notification Chain
    notified_guardians_count = 0
    links_res = await db.execute(select(AdultChildLink).where(AdultChildLink.child_id == child.id))
    links = links_res.scalars().all()

    for link in links:
        adult_res = await db.execute(select(Adult).where(Adult.id == link.adult_id))
        adult = adult_res.scalar_one_or_none()
        if adult and adult.user_id:
            notif = Notification(
                user_id=adult.user_id,
                notification_type="sos_alert",
                title=f"🚨 EMERGENCY: SOS Triggered by {child.display_name}",
                body=f"Your linked child {child.display_name} has triggered an SOS emergency alert at {location_str}.",
                data={
                    "sos_id": str(sos_event.id),
                    "case_id": str(case.id),
                    "protected_case_id": case.protected_case_id,
                    "child_id": str(child.id),
                    "child_name": child.display_name,
                    "latitude": data.latitude,
                    "longitude": data.longitude
                }
            )
            db.add(notif)
            notified_guardians_count += 1

    # Also notify assigned moderator if any
    if case.moderator_id:
        mod_res = await db.execute(select(Moderator).where(Moderator.id == case.moderator_id))
        mod = mod_res.scalar_one_or_none()
        if mod and mod.user_id:
            mod_notif = Notification(
                user_id=mod.user_id,
                notification_type="sos_alert_moderator",
                title=f"🚨 EMERGENCY: SOS in Case {case.protected_case_id}",
                body=f"Child {child.display_name} triggered an emergency SOS at {location_str}.",
                data={"sos_id": str(sos_event.id), "case_id": str(case.id)}
            )
            db.add(mod_notif)

    await db.commit()
    await db.refresh(sos_event)

    return SOSEventOut(
        id=sos_event.id,
        child_id=child.id,
        case_id=case.id,
        protected_case_id=case.protected_case_id,
        latitude=sos_event.latitude,
        longitude=sos_event.longitude,
        accuracy=sos_event.accuracy,
        location_address=sos_event.location_address,
        status=sos_event.status,
        message=sos_event.message,
        child_name=child.display_name,
        protected_child_id=child.protected_child_id,
        notified_guardians_count=notified_guardians_count,
        created_at=sos_event.created_at,
        resolved_at=sos_event.resolved_at,
        resolved_by=sos_event.resolved_by
    )

async def resolve_sos(
    db: AsyncSession,
    sos_id: uuid.UUID,
    resolver_user_id: Optional[uuid.UUID] = None,
    message: Optional[str] = None
) -> SOSEventOut:
    res = await db.execute(select(SOSEvent).where(SOSEvent.id == sos_id))
    sos_event = res.scalar_one_or_none()
    if not sos_event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SOS Event not found")

    sos_event.status = "resolved"
    sos_event.resolved_at = datetime.now(timezone.utc)
    sos_event.resolved_by = resolver_user_id
    if message:
        sos_event.message = f"{sos_event.message or ''} | Resolution: {message}".strip()

    await db.commit()
    await db.refresh(sos_event)

    # Get child info
    child_res = await db.execute(select(Child).where(Child.id == sos_event.child_id))
    child = child_res.scalar_one_or_none()

    # Get case info
    case_res = await db.execute(select(Case).where(Case.id == sos_event.case_id))
    case = case_res.scalar_one_or_none()

    return SOSEventOut(
        id=sos_event.id,
        child_id=sos_event.child_id,
        case_id=sos_event.case_id,
        protected_case_id=case.protected_case_id if case else None,
        latitude=sos_event.latitude,
        longitude=sos_event.longitude,
        accuracy=sos_event.accuracy,
        location_address=sos_event.location_address,
        status=sos_event.status,
        message=sos_event.message,
        child_name=child.display_name if child else "Child",
        protected_child_id=child.protected_child_id if child else None,
        created_at=sos_event.created_at,
        resolved_at=sos_event.resolved_at,
        resolved_by=sos_event.resolved_by
    )

async def get_sos_by_id(db: AsyncSession, sos_id: uuid.UUID) -> Optional[SOSEventOut]:
    res = await db.execute(select(SOSEvent).where(SOSEvent.id == sos_id))
    sos = res.scalar_one_or_none()
    if not sos:
        return None

    child_res = await db.execute(select(Child).where(Child.id == sos.child_id))
    child = child_res.scalar_one_or_none()

    case_res = await db.execute(select(Case).where(Case.id == sos.case_id))
    case = case_res.scalar_one_or_none()

    return SOSEventOut(
        id=sos.id,
        child_id=sos.child_id,
        case_id=sos.case_id,
        protected_case_id=case.protected_case_id if case else None,
        latitude=sos.latitude,
        longitude=sos.longitude,
        accuracy=sos.accuracy,
        location_address=sos.location_address,
        status=sos.status,
        message=sos.message,
        child_name=child.display_name if child else "Child",
        protected_child_id=child.protected_child_id if child else None,
        created_at=sos.created_at,
        resolved_at=sos.resolved_at,
        resolved_by=sos.resolved_by
    )

async def get_active_sos_events(db: AsyncSession, limit: int = 50) -> List[SOSEventOut]:
    res = await db.execute(
        select(SOSEvent)
        .where(SOSEvent.status == "active")
        .order_by(SOSEvent.created_at.desc())
        .limit(limit)
    )
    events = res.scalars().all()
    results = []
    for sos in events:
        child_res = await db.execute(select(Child).where(Child.id == sos.child_id))
        child = child_res.scalar_one_or_none()

        case_res = await db.execute(select(Case).where(Case.id == sos.case_id))
        case = case_res.scalar_one_or_none()

        results.append(SOSEventOut(
            id=sos.id,
            child_id=sos.child_id,
            case_id=sos.case_id,
            protected_case_id=case.protected_case_id if case else None,
            latitude=sos.latitude,
            longitude=sos.longitude,
            accuracy=sos.accuracy,
            location_address=sos.location_address,
            status=sos.status,
            message=sos.message,
            child_name=child.display_name if child else "Child",
            protected_child_id=child.protected_child_id if child else None,
            created_at=sos.created_at,
            resolved_at=sos.resolved_at,
            resolved_by=sos.resolved_by
        ))
    return results

async def get_nearby_sos_events(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_km: float = 10.0
) -> List[SOSEventOut]:
    active_events = await get_active_sos_events(db)
    nearby = []
    for ev in active_events:
        if ev.latitude is not None and ev.longitude is not None:
            dist = haversine_distance_km(latitude, longitude, ev.latitude, ev.longitude)
            if dist <= radius_km:
                nearby.append(ev)
    return nearby
