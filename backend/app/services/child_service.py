import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status
from app.models.child import Child, AdultChildLink, Adult
from app.models.user import User
from app.schemas.child import ChildCreate, ChildUpdate
from app.core.security import generate_protected_child_id

async def create_child(db: AsyncSession, user_id: uuid.UUID, data: ChildCreate, created_by_user_id: Optional[uuid.UUID] = None) -> Child:
    while True:
        protected_id = generate_protected_child_id()
        existing = await get_child_by_protected_id(db, protected_id)
        if not existing:
            break

    new_child = Child(
        user_id=user_id,
        protected_child_id=protected_id,
        display_name=data.display_name,
        age=data.age,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        language_preference=data.language_preference,
        created_by=created_by_user_id
    )
    db.add(new_child)
    await db.commit()
    await db.refresh(new_child)
    return new_child

async def get_child_by_id(db: AsyncSession, child_id: uuid.UUID) -> Optional[Child]:
    result = await db.execute(select(Child).where(Child.id == child_id))
    return result.scalar_one_or_none()

async def get_child_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[Child]:
    result = await db.execute(select(Child).where(Child.user_id == user_id))
    return result.scalar_one_or_none()

async def get_child_by_protected_id(db: AsyncSession, protected_child_id: str) -> Optional[Child]:
    result = await db.execute(select(Child).where(Child.protected_child_id == protected_child_id))
    return result.scalar_one_or_none()

async def update_child(db: AsyncSession, child_id: uuid.UUID, data: ChildUpdate) -> Child:
    child = await get_child_by_id(db, child_id)
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)

    await db.commit()
    await db.refresh(child)
    return child

async def link_child_to_adult(db: AsyncSession, adult_id: uuid.UUID, protected_child_id: str, relationship: str) -> AdultChildLink:
    child = await get_child_by_protected_id(db, protected_child_id)
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")

    result = await db.execute(select(AdultChildLink).where(
        AdultChildLink.adult_id == adult_id,
        AdultChildLink.child_id == child.id
    ))
    existing_link = result.scalar_one_or_none()
    
    if existing_link:
        return existing_link
        
    new_link = AdultChildLink(
        adult_id=adult_id,
        child_id=child.id,
        relationship=relationship,
        linked_at=datetime.utcnow()
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    
    # Reload with child relationship if needed
    result = await db.execute(select(AdultChildLink).where(AdultChildLink.id == new_link.id))
    new_link = result.scalar_one_or_none()
    return new_link

async def get_children_for_adult(db: AsyncSession, adult_id: uuid.UUID) -> List[Child]:
    result = await db.execute(
        select(Child).join(AdultChildLink).where(AdultChildLink.adult_id == adult_id)
    )
    return list(result.scalars().all())

async def get_adults_for_child(db: AsyncSession, child_id: uuid.UUID) -> List[Adult]:
    result = await db.execute(
        select(Adult).join(AdultChildLink).where(AdultChildLink.child_id == child_id)
    )
    return list(result.scalars().all())

async def nominate_trusted_adult(
    db: AsyncSession,
    child_id: uuid.UUID,
    adult_identifier: str,
    relationship_label: str,
    reason: Optional[str] = None
) -> AdultChildLink:
    """
    Child nominates an alternate trusted adult (e.g. aunt, teacher, trusted neighbor)
    outside primary household guardians for confidential protection and safe distress routing.
    """
    child = await get_child_by_id(db, child_id)
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child record not found")

    # Find the target adult user
    clean_id = adult_identifier.strip().lower()
    user_res = await db.execute(
        select(User).where(or_(User.email == clean_id, User.phone == adult_identifier.strip()))
    )
    user = user_res.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registered adult found with identifier '{adult_identifier}'. The trusted adult must first register on the platform."
        )

    # Find or create Adult profile
    adult_res = await db.execute(select(Adult).where(Adult.user_id == user.id))
    adult = adult_res.scalar_one_or_none()
    if not adult:
        adult = Adult(
            user_id=user.id,
            phone=user.phone,
            emergency_contacts=[]
        )
        db.add(adult)
        await db.commit()
        await db.refresh(adult)

    # Check existing link
    link_res = await db.execute(
        select(AdultChildLink).where(
            AdultChildLink.adult_id == adult.id,
            AdultChildLink.child_id == child.id
        )
    )
    link = link_res.scalar_one_or_none()
    if link:
        link.is_alternate_trusted_adult = True
        link.relationship_label = relationship_label
        link.nomination_status = "PENDING_VETTING"
        link.vetting_notes = f"Re-nominated. Reason: {reason or 'None provided'}"
        await db.commit()
        await db.refresh(link)
        return link

    new_link = AdultChildLink(
        adult_id=adult.id,
        child_id=child.id,
        relationship="trusted_adult",
        is_primary=False,
        is_verified=False,
        is_alternate_trusted_adult=True,
        nomination_status="PENDING_VETTING",
        relationship_label=relationship_label,
        vetting_notes=f"Nomination Reason: {reason or 'None provided'}",
        linked_at=datetime.utcnow()
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link

async def review_trusted_adult_nomination(
    db: AsyncSession,
    link_id: uuid.UUID,
    moderator_id: uuid.UUID,
    approved: bool,
    vetting_notes: Optional[str] = None
) -> AdultChildLink:
    """
    Moderator reviews and approves/rejects a nominated trusted adult.
    """
    link_res = await db.execute(select(AdultChildLink).where(AdultChildLink.id == link_id))
    link = link_res.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nomination link not found")

    link.nomination_status = "APPROVED" if approved else "REJECTED"
    link.is_verified = approved
    link.vetted_by_moderator_id = moderator_id
    link.vetted_at = datetime.utcnow()
    link.vetting_notes = vetting_notes or ("Vetting approved by safety moderator" if approved else "Vetting rejected")

    await db.commit()
    await db.refresh(link)
    return link

async def get_trusted_adults_for_child(
    db: AsyncSession,
    child_id: uuid.UUID
) -> List[Dict[str, Any]]:
    """
    Fetch all approved and pending trusted adults for a child.
    """
    result = await db.execute(
        select(AdultChildLink, Adult, User)
        .join(Adult, AdultChildLink.adult_id == Adult.id)
        .join(User, Adult.user_id == User.id)
        .where(
            AdultChildLink.child_id == child_id,
            or_(
                AdultChildLink.is_alternate_trusted_adult == True,
                AdultChildLink.is_primary == True
            )
        )
    )

    trusted = []
    for link, adult, user in result.all():
        trusted.append({
            "link_id": link.id,
            "adult_id": adult.id,
            "child_id": link.child_id,
            "adult_name": user.full_name or "Trusted Adult",
            "adult_email": user.email,
            "adult_phone": user.phone or adult.phone,
            "relationship": link.relationship,
            "relationship_label": link.relationship_label or link.relationship,
            "is_alternate_trusted_adult": link.is_alternate_trusted_adult,
            "nomination_status": link.nomination_status,
            "linked_at": link.linked_at,
            "vetted_at": link.vetted_at
        })
    return trusted
