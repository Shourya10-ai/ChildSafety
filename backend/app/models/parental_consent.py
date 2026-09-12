from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class ParentalConsent(Base):
    """
    Parental Consent Record under Section 9 of the Digital Personal Data Protection (DPDP) Act, 2023.
    Requires verifiable parental consent prior to processing a child's personal data.
    """
    __tablename__ = "parental_consents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    parent_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("children.id", ondelete="CASCADE"),
        index=True
    )
    consent_type: Mapped[str] = mapped_column(String(50), default="CHILD_ACCOUNT_CREATION")
    consent_status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, REVOKED
    consent_version: Mapped[str] = mapped_column(String(20), default="v1.0")
    verification_method: Mapped[str] = mapped_column(String(50), default="AFFIRMATION_CHECK")  # AFFIRMATION_CHECK, OTP_VERIFIED, BIOMETRIC_AUTH
    statutory_notice_accepted: Mapped[bool] = mapped_column(Boolean, default=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
