import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.case import Report, Case, Incident
from app.models.child import Child
from app.schemas.report import ReportCreate, ReportSubmissionResponse
from app.schemas.incident import IncidentCreate, IncidentType, IncidentSeverity
from app.services.case_service import get_or_create_active_case_for_child
from app.services.incident_service import create_incident
from app.core.security import generate_protected_child_id

async def submit_report(
    db: AsyncSession,
    data: ReportCreate,
    reporter_user_id: Optional[uuid.UUID] = None,
    reporter_role: str = "child"
) -> ReportSubmissionResponse:
    # 1. Resolve child_id
    child_id = data.child_id
    if not child_id and reporter_user_id:
        res = await db.execute(select(Child).where(Child.user_id == reporter_user_id))
        child = res.scalar_one_or_none()
        if child:
            child_id = child.id

    if not child_id:
        # Check if an anonymous child placeholder exists or create one
        res = await db.execute(select(Child).where(Child.display_name == "Anonymous Reporter").limit(1))
        anon_child = res.scalar_one_or_none()
        if not anon_child:
            anon_pid = generate_protected_child_id()
            anon_child = Child(
                protected_child_id=anon_pid,
                display_name="Anonymous Reporter",
                age=12
            )
            db.add(anon_child)
            await db.commit()
            await db.refresh(anon_child)
        child_id = anon_child.id

    # 2. Map category string to IncidentType enum safely
    cat_str = data.category.lower().replace(" ", "_")
    matched_type = IncidentType.OTHER
    for it in IncidentType:
        if it.value in cat_str or cat_str in it.value:
            matched_type = it
            break

    # 3. Create or attach to active case
    platform_info = f" on {data.platform}" if data.platform else ""
    case = await get_or_create_active_case_for_child(
        db,
        child_id=child_id,
        title=f"Report: {matched_type.value.replace('_', ' ').title()}{platform_info}",
        description=data.content[:200]
    )

    # 4. Create Incident linked to case
    incident = Incident(
        case_id=case.id,
        incident_type=matched_type.value,
        severity=IncidentSeverity.MEDIUM.value,
        description=f"Platform: {data.platform or 'Unspecified'}\nDetails: {data.content}",
        trust_level="unverified",
        source="anonymous" if data.is_anonymous else reporter_role,
        is_verified=False
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    # 5. Create Report record
    reporter_type = "anonymous" if data.is_anonymous else reporter_role
    report = Report(
        incident_id=incident.id,
        case_id=case.id,
        reporter_id=None if data.is_anonymous else reporter_user_id,
        reporter_type=reporter_type,
        content=data.content,
        is_anonymous=data.is_anonymous,
        status="submitted"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportSubmissionResponse(
        report_id=report.id,
        case_id=case.id,
        protected_case_id=case.protected_case_id,
        status=report.status,
        message="Your report has been received. A caring safety moderator is reviewing it."
    )

async def list_reports(db: AsyncSession, limit: int = 50, offset: int = 0) -> List[Report]:
    res = await db.execute(
        select(Report)
        .order_by(Report.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(res.scalars().all())

async def get_report_by_id(db: AsyncSession, report_id: uuid.UUID) -> Optional[Report]:
    res = await db.execute(select(Report).where(Report.id == report_id))
    return res.scalar_one_or_none()
