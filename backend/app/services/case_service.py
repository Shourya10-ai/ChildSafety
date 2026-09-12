import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from app.models.case import Case, ModeratorNote, Incident
from app.models.moderator import Moderator, Assignment
from app.models.escalation import Escalation
from app.schemas.case import CaseCreate, CaseUpdate, CaseStatus
from app.schemas.moderator import ModeratorNoteCreate, EscalationCreate
from app.core.security import generate_protected_case_id

async def get_or_assign_moderator_for_child(db: AsyncSession, child_id: uuid.UUID) -> Optional[Moderator]:
    """
    Core Innovation: Persistent Moderator Relationship.
    Ensures the same moderator stays with a child across all interactions/cases.
    If no moderator is assigned yet, assigns the available moderator with the least load.
    """
    # 1. Check existing active assignment for this child
    res = await db.execute(
        select(Assignment).where(
            and_(Assignment.child_id == child_id, Assignment.is_active == True)
        )
    )
    assignment = res.scalar_one_or_none()
    if assignment:
        mod_res = await db.execute(select(Moderator).where(Moderator.id == assignment.moderator_id))
        mod = mod_res.scalar_one_or_none()
        if mod:
            return mod

    # 2. If no assignment, find available moderator with lowest workload
    res = await db.execute(
        select(Moderator)
        .where(and_(Moderator.is_available == True, Moderator.active_case_count < Moderator.max_cases))
        .order_by(Moderator.active_case_count.asc())
        .limit(1)
    )
    moderator = res.scalar_one_or_none()
    if moderator:
        # Create new permanent assignment
        new_assignment = Assignment(
            child_id=child_id,
            moderator_id=moderator.id,
            is_active=True
        )
        db.add(new_assignment)
        moderator.active_case_count += 1
        await db.commit()
        await db.refresh(moderator)
        return moderator

    return None

async def get_or_create_active_case_for_child(
    db: AsyncSession,
    child_id: uuid.UUID,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: str = "medium"
) -> Case:
    """
    Longitudinal Case Intelligence:
    Attaches new reports/incidents to an existing active case, or opens a new case if none active.
    """
    # Check for active case (open or investigating)
    res = await db.execute(
        select(Case).where(
            and_(
                Case.child_id == child_id,
                Case.status.in_(["open", "investigating"])
            )
        ).order_by(Case.created_at.desc())
    )
    existing_case = res.scalar_one_or_none()
    if existing_case:
        return existing_case

    # Generate unique protected case ID
    while True:
        pid = generate_protected_case_id()
        existing_pid = await get_case_by_protected_id(db, pid)
        if not existing_pid:
            break

    # Get or assign persistent moderator
    moderator = await get_or_assign_moderator_for_child(db, child_id)
    moderator_id = moderator.id if moderator else None

    new_case = Case(
        child_id=child_id,
        moderator_id=moderator_id,
        protected_case_id=pid,
        status="open",
        priority=priority,
        title=title or "Reported Incident",
        description=description or "Case auto-generated from incoming child safety report."
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    return new_case

async def create_case(db: AsyncSession, data: CaseCreate) -> Case:
    while True:
        pid = generate_protected_case_id()
        existing_pid = await get_case_by_protected_id(db, pid)
        if not existing_pid:
            break

    moderator = await get_or_assign_moderator_for_child(db, data.child_id)
    new_case = Case(
        child_id=data.child_id,
        moderator_id=moderator.id if moderator else None,
        protected_case_id=pid,
        status="open",
        priority=data.priority.value,
        risk_level=data.risk_level,
        risk_score=data.risk_score,
        title=data.title,
        description=data.description
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)
    return new_case

async def get_case_by_id(db: AsyncSession, case_id: uuid.UUID) -> Optional[Case]:
    res = await db.execute(select(Case).where(Case.id == case_id))
    return res.scalar_one_or_none()

async def get_case_by_protected_id(db: AsyncSession, protected_case_id: str) -> Optional[Case]:
    res = await db.execute(select(Case).where(Case.protected_case_id == protected_case_id))
    return res.scalar_one_or_none()

async def list_cases(
    db: AsyncSession,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    child_id: Optional[uuid.UUID] = None,
    moderator_id: Optional[uuid.UUID] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Case]:
    query = select(Case)
    conditions = []
    if status:
        conditions.append(Case.status == status)
    if priority:
        conditions.append(Case.priority == priority)
    if child_id:
        conditions.append(Case.child_id == child_id)
    if moderator_id:
        conditions.append(Case.moderator_id == moderator_id)
    
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(Case.created_at.desc()).limit(limit).offset(offset)
    res = await db.execute(query)
    return list(res.scalars().all())

async def update_case(db: AsyncSession, case_id: uuid.UUID, data: CaseUpdate) -> Case:
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    update_dict = data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if hasattr(value, "value"):
            setattr(case, field, value.value)
        else:
            setattr(case, field, value)

    await db.commit()
    await db.refresh(case)
    return case

async def add_moderator_note(
    db: AsyncSession,
    case_id: uuid.UUID,
    moderator_id: uuid.UUID,
    data: ModeratorNoteCreate
) -> ModeratorNote:
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    note = ModeratorNote(
        case_id=case_id,
        moderator_id=moderator_id,
        content=data.content,
        note_type=data.note_type.value
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

async def get_case_notes(db: AsyncSession, case_id: uuid.UUID) -> List[ModeratorNote]:
    res = await db.execute(
        select(ModeratorNote)
        .where(ModeratorNote.case_id == case_id)
        .order_by(ModeratorNote.created_at.asc())
    )
    return list(res.scalars().all())

async def escalate_case(
    db: AsyncSession,
    case_id: uuid.UUID,
    moderator_id: uuid.UUID,
    data: EscalationCreate
) -> Escalation:
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    escalation = Escalation(
        case_id=case_id,
        from_moderator_id=moderator_id,
        reason=data.reason,
        status="pending",
        priority=data.priority,
        notes=data.notes
    )
    case.status = "escalated"
    db.add(escalation)
    await db.commit()
    await db.refresh(escalation)
    return escalation

async def transition_case_status(
    db: AsyncSession,
    case_id: uuid.UUID,
    to_status: CaseStatus,
    reason: str,
    actor_id: Optional[uuid.UUID] = None,
    actor_role: str = "moderator",
    statutory_reference: Optional[str] = None,
    dismissal_category: Optional[str] = None
) -> Case:
    case = await get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    current_status = case.status

    # Rule 1: Human-in-the-loop escalation guard:
    # Cannot escalate to legal/authorities directly from unreviewed AI flag
    if to_status == CaseStatus.ESCALATED:
        if current_status in [CaseStatus.AI_FLAGGED.value, CaseStatus.PENDING_HUMAN_REVIEW.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Human-in-the-Loop Violation: AI-flagged cases cannot be escalated to authorities without prior human moderator confirmation."
            )
        if actor_role not in ["moderator", "authority", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Statutory escalation requires certified human moderator or authority credentials."
            )

    # Rule 2: AI Flag gate:
    # If case is AI_FLAGGED or PENDING_HUMAN_REVIEW, it can only transition to MODERATOR_CONFIRMED or FALSE_POSITIVE_DISMISSED
    if current_status in [CaseStatus.AI_FLAGGED.value, CaseStatus.PENDING_HUMAN_REVIEW.value]:
        if to_status not in [CaseStatus.MODERATOR_CONFIRMED, CaseStatus.FALSE_POSITIVE_DISMISSED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transition from '{current_status}'. Must be confirmed or dismissed by a human moderator."
            )

    # If confirmed by moderator, attach verification note
    if to_status == CaseStatus.MODERATOR_CONFIRMED:
        note_text = f"Moderator confirmed risk flag. Rationale: {reason}"
        if statutory_reference:
            note_text += f" | Statutory Basis: {statutory_reference}"
        if actor_id:
            db.add(ModeratorNote(
                case_id=case.id,
                moderator_id=actor_id,
                content=note_text,
                note_type="verification"
            ))

    # If dismissed as false positive, attach audit note
    if to_status == CaseStatus.FALSE_POSITIVE_DISMISSED:
        audit_text = f"False positive dismissed. Reason: {reason}"
        if dismissal_category:
            audit_text += f" | Category: {dismissal_category}"
        if actor_id:
            db.add(ModeratorNote(
                case_id=case.id,
                moderator_id=actor_id,
                content=audit_text,
                note_type="audit"
            ))

    case.status = to_status.value
    await db.commit()
    await db.refresh(case)
    return case

