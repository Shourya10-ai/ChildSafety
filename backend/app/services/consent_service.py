import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from app.models.parental_consent import ParentalConsent
from app.models.child import Child
from app.schemas.parental_consent import ParentalConsentCreate, ParentalConsentOut, ConsentVerificationResponse

async def record_parental_consent(
    db: AsyncSession,
    parent_user_id: uuid.UUID,
    data: ParentalConsentCreate,
    ip_address: Optional[str] = None
) -> ParentalConsent:
    # 1. Verify child profile exists
    res = await db.execute(select(Child).where(Child.id == data.child_id))
    child = res.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child profile not found")

    if not data.statutory_notice_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DPDP Act 2023 compliance requires explicit acceptance of statutory notice for processing child personal data."
        )

    # 2. Record affirmative consent
    consent = ParentalConsent(
        parent_user_id=parent_user_id,
        child_id=data.child_id,
        consent_type=data.consent_type,
        consent_status="ACTIVE",
        consent_version=data.consent_version,
        verification_method=data.verification_method,
        statutory_notice_accepted=data.statutory_notice_accepted,
        ip_address=ip_address
    )
    db.add(consent)
    await db.commit()
    await db.refresh(consent)
    return consent

async def check_child_has_valid_consent(
    db: AsyncSession,
    child_id: uuid.UUID
) -> ConsentVerificationResponse:
    res = await db.execute(
        select(ParentalConsent)
        .where(
            and_(
                ParentalConsent.child_id == child_id,
                ParentalConsent.consent_status == "ACTIVE"
            )
        )
        .order_by(ParentalConsent.timestamp.desc())
        .limit(1)
    )
    consent = res.scalar_one_or_none()

    if consent:
        return ConsentVerificationResponse(
            child_id=child_id,
            has_valid_consent=True,
            consent_type=consent.consent_type,
            verified_at=consent.timestamp
        )
    return ConsentVerificationResponse(
        child_id=child_id,
        has_valid_consent=False,
        consent_type=None,
        verified_at=None
    )
