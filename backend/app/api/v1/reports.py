import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from app.core.dependencies import get_db, get_redis, require_roles
from app.core.rate_limiter import check_anonymous_report_rate_limit
from app.models.user import User
from app.schemas.report import ReportCreate, ReportOut, ReportSubmissionResponse
from app.services import report_service

router = APIRouter()
optional_bearer = HTTPBearer(auto_error=False)

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
    db: AsyncSession = Depends(get_db),
    redis_client = Depends(get_redis)
) -> Optional[User]:
    if not credentials:
        return None
    try:
        from app.services.auth_service import AuthService
        auth_service = AuthService(db, redis_client)
        return await auth_service.get_current_user_from_token(credentials.credentials)
    except Exception:
        return None

@router.post("/", response_model=ReportSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_safety_report(
    data: ReportCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    optional_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Submits a child safety report. Can be anonymous or authenticated.
    Protected by Redis sliding-window rate limiter & content hash deduplication.
    Automatically triages the report, creates an incident, attaches to the child's active case,
    and assigns a persistent moderator.
    """
    report_text = data.content or data.details or data.category
    await check_anonymous_report_rate_limit(
        request=request,
        redis_client=redis_client,
        content=report_text,
        category=data.category
    )
    reporter_id = optional_user.id if optional_user else None
    reporter_role = optional_user.role if optional_user else "child"
    return await report_service.submit_report(
        db,
        data,
        reporter_user_id=reporter_id,
        reporter_role=reporter_role
    )

@router.get("/", response_model=List[ReportOut])
async def list_reports(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "admin", "authority"))
):
    return await report_service.list_reports(db, limit=limit, offset=offset)

@router.get("/{id}", response_model=ReportOut)
async def get_report(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("moderator", "admin", "authority"))
):
    report = await report_service.get_report_by_id(db, id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report
