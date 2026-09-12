import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.parental_consent import ParentalConsentCreate, ParentalConsentOut, ConsentVerificationResponse
from app.services import consent_service

router = APIRouter()

@router.post("/", response_model=ParentalConsentOut, status_code=status.HTTP_201_CREATED)
async def submit_parental_consent(
    data: ParentalConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submits verifiable parental consent under Section 9 of DPDP Act 2023.
    """
    client_ip = request.client.host if request.client else None
    return await consent_service.record_parental_consent(
        db=db,
        parent_user_id=current_user.id,
        data=data,
        ip_address=client_ip
    )

@router.get("/child/{child_id}", response_model=ConsentVerificationResponse)
async def verify_child_consent(
    child_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verifies whether a child has active, unrevoked parental consent on file.
    """
    return await consent_service.check_child_has_valid_consent(db, child_id)
