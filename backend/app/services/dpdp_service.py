import uuid
from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, delete
from fastapi import HTTPException, status

from app.models.user import User
from app.models.child import Child, AdultChildLink
from app.models.parental_consent import ParentalConsent
from app.models.notification import Notification
from app.models.evidence import Evidence
from app.models.case import Case
from app.models.audit import AuditLog
from app.schemas.dpdp import (
    DpdpRightsResponse, ErasureRequestCreate, ErasureRequestOut,
    AgeOfMajorityTransitionResult, DataRetentionSweepResult
)

async def check_age_of_majority_transitions(
    db: AsyncSession
) -> AgeOfMajorityTransitionResult:
    """
    Scans for children who have turned 18.
    Statutory DPDP Act 2023 Enforcement:
    1. Parental consent automatically lapses (EXPIRED_AGE_OF_MAJORITY).
    2. All guardian links in adult_child_links are severed.
    3. User account transitions from 'child' to 'adult' self-custody.
    4. Immutable audit trail created.
    """
    today = date.today()
    
    # Query children with DOB
    res = await db.execute(select(Child).where(Child.date_of_birth.is_not(None)))
    children = res.scalars().all()

    transitioned_ids = []
    severs_count = 0

    for child in children:
        dob = child.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if age >= 18:
            # Check if user role is still 'child'
            if child.user_id:
                u_res = await db.execute(select(User).where(User.id == child.user_id))
                user = u_res.scalar_one_or_none()
                if user and user.role == "child":
                    # 1. Update user role to adult
                    user.role = "adult"
                    
                    # 2. Expire parental consent
                    await db.execute(
                        update(ParentalConsent)
                        .where(ParentalConsent.child_id == child.id)
                        .values(consent_status="EXPIRED_AGE_OF_MAJORITY")
                    )

                    # 3. Sever all guardian links
                    del_res = await db.execute(
                        delete(AdultChildLink).where(AdultChildLink.child_id == child.id)
                    )
                    severs_count += del_res.rowcount or 0

                    # 4. Audit Log
                    audit = AuditLog(
                        action="DPDP_AGE_OF_MAJORITY_TRANSITION",
                        user_id=user.id,
                        resource_type="child",
                        resource_id=str(child.id),
                        details={
                            "message": f"User {user.email} reached age {age}. Parental consent severed; account granted full adult DPDP self-custody.",
                            "transitioned_at": datetime.utcnow().isoformat()
                        }
                    )
                    db.add(audit)
                    transitioned_ids.append(str(child.id))

    await db.commit()

    return AgeOfMajorityTransitionResult(
        total_evaluated=len(children),
        transitions_executed=len(transitioned_ids),
        transitioned_child_ids=transitioned_ids,
        severs_executed=severs_count,
        timestamp=datetime.utcnow()
    )

async def run_dual_track_data_retention_sweep(
    db: AsyncSession
) -> DataRetentionSweepResult:
    """
    Dual-Track Retention Sweep:
    - Track 1 (Operational): Purges transient read notifications and logs older than 90 days.
    - Track 2 (Forensic): Retains encrypted evidence ledgers under 7-year POCSO / BSA statutory requirement.
    """
    cutoff_90_days = datetime.utcnow() - timedelta(days=90)

    # Purge read notifications older than 90 days
    stmt = delete(Notification).where(
        and_(Notification.is_read == True, Notification.created_at < cutoff_90_days)
    )
    res = await db.execute(stmt)
    purged_count = res.rowcount or 0

    # Count preserved forensic evidence records
    ev_count_res = await db.execute(select(func.count(Evidence.id)))
    preserved_count = ev_count_res.scalar() or 0

    await db.commit()

    return DataRetentionSweepResult(
        operational_logs_purged=purged_count,
        forensic_records_preserved=preserved_count,
        timestamp=datetime.utcnow()
    )

async def get_user_dpdp_rights(
    db: AsyncSession,
    user: User
) -> DpdpRightsResponse:
    is_adult = (user.role in ["adult", "moderator", "authority", "admin"])
    
    consent_status = None
    has_active_consent = False
    
    if user.role == "child":
        c_res = await db.execute(select(Child).where(Child.user_id == user.id))
        child = c_res.scalar_one_or_none()
        if child:
            pc_res = await db.execute(
                select(ParentalConsent).where(ParentalConsent.child_id == child.id).order_by(ParentalConsent.timestamp.desc())
            )
            consent = pc_res.scalar_one_or_none()
            if consent:
                consent_status = consent.consent_status
                has_active_consent = (consent.consent_status == "ACTIVE")

    # Check for active case or forensic lock
    forensic_locked = False
    if user.role == "child":
        c_res = await db.execute(select(Child).where(Child.user_id == user.id))
        child = c_res.scalar_one_or_none()
        if child:
            cases_res = await db.execute(
                select(Case).where(and_(Case.child_id == child.id, Case.status.in_(["open", "investigating", "escalated"])))
            )
            if cases_res.first():
                forensic_locked = True

    rights = [
        "Right to Access Summary of Personal Data (Section 11, DPDP Act 2023)",
        "Right to Correction and Updating of Personal Data (Section 12(1))",
        "Right to Grievance Redressal (Section 13)",
        "Right to Nominate Representative in Event of Death or Incapacity (Section 14)",
        "Right to Erasure (Section 12(2) - Human-Gated for Statutory Child Protection Evidence)"
    ]

    return DpdpRightsResponse(
        user_id=user.id,
        email=user.email,
        role=user.role,
        is_adult_self_custody=is_adult,
        active_consent_on_file=has_active_consent,
        consent_status=consent_status,
        eligible_for_erasure=not forensic_locked,
        forensic_retention_locked=forensic_locked,
        retention_statute="DPDP Act 2023 (Section 8) & Bharatiya Sakshya Adhiniyam 2023 (Section 63)",
        dpdp_statutory_rights=rights
    )

async def submit_erasure_request(
    db: AsyncSession,
    user: User,
    data: ErasureRequestCreate
) -> ErasureRequestOut:
    req_id = f"DPDP-DEL-{uuid.uuid4().hex[:8].upper()}"
    
    # Check forensic locks
    rights = await get_user_dpdp_rights(db, user)
    
    status_label = "PENDING_STATUTORY_REVIEW"
    notes = "Request queued for legal and moderator review under DPDP Act 2023 Section 12."
    if rights.forensic_retention_locked:
        status_label = "REJECTED_FORENSIC_LOCK"
        notes = "Active child protection case or POCSO Section 19 evidence is on file. Forensic evidence cannot be purged."

    # Audit entry
    audit = AuditLog(
        action="DPDP_ERASURE_REQUEST",
        user_id=user.id,
        resource_type="dpdp_erasure",
        resource_id=req_id,
        details={
            "request_id": req_id,
            "status": status_label,
            "reason": data.reason,
            "scope": data.scope,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    db.add(audit)
    await db.commit()

    return ErasureRequestOut(
        request_id=req_id,
        user_id=user.id,
        status=status_label,
        submitted_at=datetime.utcnow(),
        statutory_notes=notes
    )
