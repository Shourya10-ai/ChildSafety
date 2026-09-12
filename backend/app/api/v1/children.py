from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.core.dependencies import get_db, get_current_user, get_current_active_user, require_roles
from app.models.user import User
from app.schemas.child import ChildCreate, ChildUpdate, ChildOut, LinkChildRequest, ChildLinkOut
from app.schemas.adult import AdultOut
from app.services import child_service, adult_service

router = APIRouter(prefix="/children", tags=["Child Management"])

@router.post("/", response_model=ChildOut, status_code=status.HTTP_201_CREATED)
async def create_child_profile(
    data: ChildCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role == "child":
        # Self-registration logic
        existing = await child_service.get_child_by_user_id(db, current_user.id)
        if existing:
            raise HTTPException(status_code=400, detail="Child profile already exists for this user")
        return await child_service.create_child(db, user_id=current_user.id, data=data)
    else:
        # Adult creating a child profile
        return await child_service.create_child(db, user_id=current_user.id, data=data, created_by_user_id=current_user.id)

@router.get("/me", response_model=ChildOut)
async def get_my_child_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    child = await child_service.get_child_by_user_id(db, current_user.id)
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found")
    return child

@router.get("/{child_id}", response_model=ChildOut)
async def get_child_profile(
    child_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    child = await child_service.get_child_by_id(db, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Check permissions
    if current_user.role in ["moderator", "authority", "admin"]:
        return child
        
    if current_user.id == child.user_id:
        return child
        
    # Check if linked adult
    adult = await adult_service.get_adult_by_user_id(db, current_user.id)
    if adult:
        linked_children = await child_service.get_children_for_adult(db, adult.id)
        if child.id in [c.id for c in linked_children]:
            return child
            
    raise HTTPException(status_code=403, detail="Not authorized to view this child profile")

@router.put("/{child_id}", response_model=ChildOut)
async def update_child_profile(
    child_id: uuid.UUID,
    data: ChildUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    child = await child_service.get_child_by_id(db, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
        
    if current_user.role in ["moderator", "authority", "admin"] or current_user.id == child.user_id:
        pass
    else:
        adult = await adult_service.get_adult_by_user_id(db, current_user.id)
        if adult:
            linked_children = await child_service.get_children_for_adult(db, adult.id)
            if child.id not in [c.id for c in linked_children]:
                raise HTTPException(status_code=403, detail="Not authorized to update this child profile")
        else:
             raise HTTPException(status_code=403, detail="Not authorized to update this child profile")
             
    return await child_service.update_child(db, child_id, data)

@router.post("/link", response_model=ChildLinkOut)
async def link_adult_to_child(
    data: LinkChildRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    adult = await adult_service.get_or_create_adult(db, current_user.id)
    return await child_service.link_child_to_adult(db, adult.id, data.protected_child_id, data.relationship)

@router.get("/{child_id}/adults", response_model=List[AdultOut])
async def get_linked_adults(
    child_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    child = await child_service.get_child_by_id(db, child_id)
    if not child:
         raise HTTPException(status_code=404, detail="Child not found")
         
    if current_user.role in ["moderator", "authority", "admin"] or current_user.id == child.user_id:
        return await child_service.get_adults_for_child(db, child_id)
        
    raise HTTPException(status_code=403, detail="Not authorized to view adults for this child")
