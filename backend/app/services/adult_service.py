import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.child import Adult
from app.schemas.adult import AdultUpdate, EmergencyContact

async def get_or_create_adult(db: AsyncSession, user_id: uuid.UUID) -> Adult:
    adult = await get_adult_by_user_id(db, user_id)
    if adult:
        return adult
        
    new_adult = Adult(user_id=user_id)
    db.add(new_adult)
    await db.commit()
    await db.refresh(new_adult)
    return new_adult

async def get_adult_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[Adult]:
    result = await db.execute(select(Adult).where(Adult.user_id == user_id))
    return result.scalar_one_or_none()

async def get_adult_by_id(db: AsyncSession, adult_id: uuid.UUID) -> Optional[Adult]:
    result = await db.execute(select(Adult).where(Adult.id == adult_id))
    return result.scalar_one_or_none()

async def update_adult(db: AsyncSession, adult_id: uuid.UUID, data: AdultUpdate) -> Adult:
    adult = await get_adult_by_id(db, adult_id)
    if not adult:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adult not found")

    update_data = data.model_dump(exclude_unset=True)
    if "emergency_contacts" in update_data and update_data["emergency_contacts"] is not None:
        update_data["emergency_contacts"] = [ec for ec in update_data["emergency_contacts"]]
        
    for field, value in update_data.items():
        setattr(adult, field, value)

    await db.commit()
    await db.refresh(adult)
    return adult

async def add_emergency_contact(db: AsyncSession, adult_id: uuid.UUID, contact: EmergencyContact) -> Adult:
    adult = await get_adult_by_id(db, adult_id)
    if not adult:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adult not found")
        
    current_contacts = adult.emergency_contacts or []
    current_contacts.append(contact.model_dump())
    
    adult.emergency_contacts = current_contacts
    await db.commit()
    await db.refresh(adult)
    return adult
