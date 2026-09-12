import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.models.missing_child import MissingChild, CCTVCandidate
from app.models.case import Case, ModeratorNote
from app.models.child import Child
from app.models.user import User
from app.schemas.missing_child import (
    MissingChildCreate, MissingChildOut, MissingChildDetailOut,
    SightingCreate, SightingOut
)
from app.services.case_service import get_or_create_active_case_for_child, get_or_assign_moderator_for_child
from app.core.security import generate_protected_case_id, generate_protected_child_id
from app.core.websocket_manager import ws_manager

async def report_missing_child(
    db: AsyncSession,
    data: MissingChildCreate,
    reporter: User
) -> MissingChildOut:
    # 1. Resolve or create associated Child entity
    child_id = data.child_id
    if not child_id:
        # Create a stub child record if none linked
        pid = generate_protected_child_id(data.state, data.district)
        child = Child(
            protected_child_id=pid,
            display_name=data.child_name,
            age=data.age_when_missing,
            gender=data.gender,
            state=data.state,
            district=data.district,
            is_active=True,
            setup_path="ADULT_INITIATED"
        )
        db.add(child)
        await db.commit()
        await db.refresh(child)
        child_id = child.id

    # 2. Generate a dedicated critical Missing Child Case
    pid_case = generate_protected_case_id()
    assigned_mod = await get_or_assign_moderator_for_child(db, child_id)
    
    new_case = Case(
        child_id=child_id,
        moderator_id=assigned_mod.id if assigned_mod else None,
        protected_case_id=pid_case,
        status="open",
        priority="critical",
        title=f"🚨 MISSING CHILD ALERT: {data.child_name}",
        description=f"{data.description} | Last Seen: {data.last_known_address or 'Unknown location'}"
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    # 3. Create MissingChild entity
    record = MissingChild(
        case_id=new_case.id,
        child_id=child_id,
        child_name=data.child_name,
        photo_url=data.photo_url,
        description=data.description,
        age_when_missing=data.age_when_missing,
        gender=data.gender,
        height_cm=data.height_cm,
        weight_kg=data.weight_kg,
        clothing_description=data.clothing_description,
        identifying_marks=data.identifying_marks,
        last_known_address=data.last_known_address,
        latitude=data.latitude,
        longitude=data.longitude,
        state=data.state,
        district=data.district,
        last_seen_at=data.last_seen_at or datetime.utcnow(),
        status="ACTIVE",
        reported_by_user_id=reporter.id
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # 4. Real-Time Emergency Broadcast via WebSockets
    broadcast_payload = {
        "event": "MISSING_CHILD_ALERT",
        "missing_child_id": str(record.id),
        "child_name": record.child_name,
        "age": record.age_when_missing,
        "photo_url": record.photo_url,
        "last_known_address": record.last_known_address,
        "state": record.state,
        "district": record.district,
        "timestamp": datetime.utcnow().isoformat()
    }
    await ws_manager.broadcast_to_channel(broadcast_payload, "cs:emergency")
    await ws_manager.broadcast_to_channel(broadcast_payload, "cs:broadcast")

    return MissingChildOut.model_validate(record)

async def list_active_missing_children(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
    state: Optional[str] = None,
    district: Optional[str] = None
) -> List[MissingChildOut]:
    q = select(MissingChild).where(MissingChild.status == "ACTIVE")
    if state:
        q = q.where(MissingChild.state.ilike(f"%{state}%"))
    if district:
        q = q.where(MissingChild.district.ilike(f"%{district}%"))
    q = q.order_by(MissingChild.created_at.desc()).limit(limit).offset(offset)
    
    res = await db.execute(q)
    records = res.scalars().all()
    return [MissingChildOut.model_validate(r) for r in records]

async def get_missing_child_detail(
    db: AsyncSession,
    missing_child_id: uuid.UUID
) -> MissingChildDetailOut:
    res = await db.execute(select(MissingChild).where(MissingChild.id == missing_child_id))
    child_rec = res.scalar_one_or_none()
    if not child_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing child record not found")

    # Fetch sightings
    sightings_res = await db.execute(
        select(CCTVCandidate)
        .where(CCTVCandidate.missing_child_id == missing_child_id)
        .order_by(CCTVCandidate.created_at.desc())
    )
    sightings = sightings_res.scalars().all()

    # Get linked case protected ID
    case_res = await db.execute(select(Case).where(Case.id == child_rec.case_id))
    case = case_res.scalar_one_or_none()

    out = MissingChildDetailOut.model_validate(child_rec)
    out.protected_case_id = case.protected_case_id if case else None
    out.sightings = [SightingOut.model_validate(s) for s in sightings]
    return out

async def submit_sighting(
    db: AsyncSession,
    missing_child_id: uuid.UUID,
    data: SightingCreate,
    reporter: Optional[User] = None
) -> SightingOut:
    res = await db.execute(select(MissingChild).where(MissingChild.id == missing_child_id))
    child_rec = res.scalar_one_or_none()
    if not child_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing child record not found")

    if child_rec.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This missing child case is no longer active")

    sighting = CCTVCandidate(
        missing_child_id=child_rec.id,
        image_url=data.image_url,
        location_address=data.location_address,
        latitude=data.latitude,
        longitude=data.longitude,
        captured_at=data.captured_at or datetime.utcnow(),
        source="CITIZEN_SIGHTING",
        sighting_notes=data.sighting_notes,
        reported_by_user_id=reporter.id if reporter else None,
        status="PENDING_REVIEW"
    )
    db.add(sighting)
    await db.commit()
    await db.refresh(sighting)

    # Log note in linked case
    case_res = await db.execute(select(Case).where(Case.id == child_rec.case_id))
    case = case_res.scalar_one_or_none()
    if case and case.moderator_id:
        note = ModeratorNote(
            case_id=case.id,
            moderator_id=case.moderator_id,
            content=f"New sighting submitted near {data.location_address or 'Unknown location'}. Notes: {data.sighting_notes or 'None'}",
            note_type="SIGHTING_LOG"
        )
        db.add(note)
        await db.commit()

    # Dispatch WebSocket notification to duty moderators
    event_payload = {
        "event": "SIGHTING_SUBMITTED",
        "missing_child_id": str(child_rec.id),
        "sighting_id": str(sighting.id),
        "location": data.location_address,
        "image_url": data.image_url,
        "timestamp": datetime.utcnow().isoformat()
    }
    await ws_manager.broadcast_to_role(event_payload, "moderator")

    return SightingOut.model_validate(sighting)

async def verify_sighting(
    db: AsyncSession,
    sighting_id: uuid.UUID,
    moderator: User,
    is_match: bool,
    notes: Optional[str] = None
) -> SightingOut:
    res = await db.execute(select(CCTVCandidate).where(CCTVCandidate.id == sighting_id))
    sighting = res.scalar_one_or_none()
    if not sighting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sighting candidate not found")

    sighting.status = "VERIFIED_MATCH" if is_match else "DISMISSED"
    sighting.verified_by = moderator.id
    sighting.verified_at = datetime.utcnow()
    sighting.verification_notes = notes

    await db.commit()
    await db.refresh(sighting)

    # Log note in case
    mc_res = await db.execute(select(MissingChild).where(MissingChild.id == sighting.missing_child_id))
    mc = mc_res.scalar_one_or_none()
    if mc:
        case_res = await db.execute(select(Case).where(Case.id == mc.case_id))
        case = case_res.scalar_one_or_none()
        if case and case.moderator_id:
            status_label = "VERIFIED AS MATCH" if is_match else "DISMISSED"
            note = ModeratorNote(
                case_id=case.id,
                moderator_id=case.moderator_id,
                content=f"Sighting {sighting.id} {status_label} by {moderator.full_name or 'Moderator'}. Notes: {notes or 'None'}",
                note_type="VERIFICATION"
            )
            db.add(note)
            await db.commit()

    return SightingOut.model_validate(sighting)

async def resolve_missing_child(
    db: AsyncSession,
    missing_child_id: uuid.UUID,
    moderator: User,
    resolution_notes: str
) -> MissingChildOut:
    res = await db.execute(select(MissingChild).where(MissingChild.id == missing_child_id))
    child_rec = res.scalar_one_or_none()
    if not child_rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Missing child record not found")

    child_rec.status = "FOUND"
    child_rec.resolved_at = datetime.utcnow()
    child_rec.resolution_notes = resolution_notes

    # Transition linked case to closed
    case_res = await db.execute(select(Case).where(Case.id == child_rec.case_id))
    case = case_res.scalar_one_or_none()
    if case:
        case.status = "closed"
        if case.moderator_id:
            note = ModeratorNote(
                case_id=case.id,
                moderator_id=case.moderator_id,
                content=f"MISSING CHILD CASE RESOLVED (FOUND): {resolution_notes}",
                note_type="RESOLUTION"
            )
            db.add(note)
            await db.commit()

    await db.commit()
    await db.refresh(child_rec)

    # Dispatch resolution broadcast
    resolve_payload = {
        "event": "MISSING_CHILD_RESOLVED",
        "missing_child_id": str(child_rec.id),
        "child_name": child_rec.child_name,
        "status": "FOUND",
        "resolved_at": child_rec.resolved_at.isoformat()
    }
    await ws_manager.broadcast_to_channel(resolve_payload, "cs:broadcast")

    return MissingChildOut.model_validate(child_rec)
