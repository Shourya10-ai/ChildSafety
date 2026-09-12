from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.schemas.dpdp import (
    DpdpRightsResponse, ErasureRequestCreate, ErasureRequestOut,
    AgeOfMajorityTransitionResult, DataRetentionSweepResult
)
from app.services import dpdp_service

router = APIRouter(prefix="/dpdp", tags=["DPDP Act 2023 Compliance & 18+ Rights"])

@router.get("/rights", response_model=DpdpRightsResponse)
async def get_dpdp_rights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns user's statutory data rights summary under the Digital Personal Data Protection (DPDP) Act 2023,
    including consent validity, data access status, and forensic evidence locks.
    """
    return await dpdp_service.get_user_dpdp_rights(db, current_user)

@router.post("/erasure-request", response_model=ErasureRequestOut, status_code=status.HTTP_201_CREATED)
async def submit_erasure_request(
    data: ErasureRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submits a Right-to-Erasure request under Section 12(2) of the DPDP Act 2023.
    Child protection records are human-gated against statutory retention requirements under Section 63 BSA 2023.
    """
    return await dpdp_service.submit_erasure_request(db, current_user, data)

@router.post("/run-transitions", response_model=AgeOfMajorityTransitionResult)
async def run_age_of_majority_sweep(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "moderator"]))
):
    """
    Automated administrative sweep: Scans for users who have attained the age of majority (18 years).
    Automatically severs guardian surveillance links, lapses parental consent, and promotes account to self-custody.
    """
    return await dpdp_service.check_age_of_majority_transitions(db)

@router.post("/run-retention-sweep", response_model=DataRetentionSweepResult)
async def run_retention_sweep(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "moderator"]))
):
    """
    Executes dual-track data retention purge: removes transient operational logs older than 90 days
    while cryptographically locking 7-year forensic evidence.
    """
    return await dpdp_service.run_dual_track_data_retention_sweep(db)
