import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_active_user, require_roles
from app.models.user import User
from app.schemas.risk_engine import RiskEvaluationResponse
from app.schemas.case_similarity import CaseSimilarityResponse
from app.services.risk_engine_service import RiskEngineService
from app.services.case_similarity_service import CaseSimilarityService

router = APIRouter(prefix="/risk", tags=["Predictive Risk Engine & Case Similarity"])

@router.get("/case/{case_id}", response_model=RiskEvaluationResponse)
async def evaluate_case_risk(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Executes a multi-factor risk assessment combining incident velocity,
    modus operandi severity, predator persistence, and child vulnerability.
    """
    try:
        return await RiskEngineService.evaluate_case_risk(db, case_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/child/{child_id}", response_model=RiskEvaluationResponse)
async def evaluate_child_risk(
    child_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Evaluates cumulative safety posture and active threat tier across all active cases for a child.
    """
    try:
        return await RiskEngineService.evaluate_child_risk(db, child_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/case/{case_id}/similar", response_model=CaseSimilarityResponse)
async def find_similar_cases(
    case_id: uuid.UUID,
    top_k: int = Query(5, ge=1, le=20, description="Number of top similar cases to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["moderator", "authority", "admin"]))
):
    """
    Finds Top-K similar cases across the platform using multi-dimensional matching:
    Modus Operandi tactics, shared suspect handles, and spatial-temporal clustering.
    """
    try:
        return await CaseSimilarityService.find_similar_cases(db, case_id, top_k=top_k)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
