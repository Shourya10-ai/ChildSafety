import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.models.moderator import Moderator
from app.schemas.case import CaseCreate, CaseUpdate, CaseOut, CaseDetailOut
from app.schemas.moderator import ModeratorNoteCreate, ModeratorNoteOut, EscalationCreate, EscalationOut
from app.services import case_service
from app.services import incident_service
from sqlalchemy import select

router = APIRouter()

@router.get("/", response_model=List[CaseOut])
async def list_cases(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    child_id: Optional[uuid.UUID] = Query(None),
    moderator_id: Optional[uuid.UUID] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await case_service.list_cases(
        db, status=status, priority=priority, child_id=child_id, moderator_id=moderator_id, limit=limit, offset=offset
    )

@router.post("/", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "admin", "authority"))
):
    return await case_service.create_case(db, data)

@router.get("/{id}", response_model=CaseDetailOut)
async def get_case_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    case = await case_service.get_case_by_id(db, id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    incidents = await incident_service.list_incidents_for_case(db, id)
    notes = await case_service.get_case_notes(db, id)

    moderator_name = None
    if case.moderator_id:
        res = await db.execute(select(User).join(Moderator, Moderator.user_id == User.id).where(Moderator.id == case.moderator_id))
        mod_user = res.scalar_one_or_none()
        if mod_user:
            moderator_name = mod_user.full_name

    incidents_data = [
        {
            "id": str(inc.id),
            "incident_type": inc.incident_type,
            "severity": inc.severity,
            "description": inc.description,
            "trust_level": inc.trust_level,
            "is_verified": inc.is_verified,
            "created_at": inc.created_at.isoformat()
        }
        for inc in incidents
    ]

    notes_data = [
        {
            "id": str(n.id),
            "note_type": n.note_type,
            "content": n.content,
            "created_at": n.created_at.isoformat()
        }
        for n in notes
    ]

    return CaseDetailOut(
        id=case.id,
        child_id=case.child_id,
        moderator_id=case.moderator_id,
        protected_case_id=case.protected_case_id,
        status=case.status,
        priority=case.priority,
        risk_level=case.risk_level,
        risk_score=case.risk_score,
        title=case.title,
        description=case.description,
        created_at=case.created_at,
        updated_at=case.updated_at,
        incidents=incidents_data,
        notes=notes_data,
        moderator_name=moderator_name
    )

@router.put("/{id}", response_model=CaseOut)
async def update_case(
    id: uuid.UUID,
    data: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "admin", "authority"))
):
    return await case_service.update_case(db, id, data)

@router.post("/{id}/notes", response_model=ModeratorNoteOut, status_code=status.HTTP_201_CREATED)
async def add_note(
    id: uuid.UUID,
    data: ModeratorNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "admin"))
):
    res = await db.execute(select(Moderator).where(Moderator.user_id == current_user.id))
    moderator = res.scalar_one_or_none()
    if not moderator:
        # Auto-create moderator profile for this user if needed
        moderator = Moderator(user_id=current_user.id)
        db.add(moderator)
        await db.commit()
        await db.refresh(moderator)

    return await case_service.add_moderator_note(db, id, moderator.id, data)

@router.get("/{id}/notes", response_model=List[ModeratorNoteOut])
async def get_notes(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await case_service.get_case_notes(db, id)

@router.post("/{id}/escalate", response_model=EscalationOut, status_code=status.HTTP_201_CREATED)
async def escalate(
    id: uuid.UUID,
    data: EscalationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "admin"))
):
    res = await db.execute(select(Moderator).where(Moderator.user_id == current_user.id))
    moderator = res.scalar_one_or_none()
    if not moderator:
        moderator = Moderator(user_id=current_user.id)
        db.add(moderator)
        await db.commit()
        await db.refresh(moderator)

    return await case_service.escalate_case(db, id, moderator.id, data)
