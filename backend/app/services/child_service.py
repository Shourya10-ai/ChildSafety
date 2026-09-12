import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.child import Child, AdultChildLink, Adult
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
        relationship=relationship
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
