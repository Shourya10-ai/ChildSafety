from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Text, JSON, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class SuspectEntity(Base, TimestampMixin):
    """
    Represents an offender, suspect account, digital handle, or phone number
    identified across safety reports and cases.
    """
    __tablename__ = "suspect_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    identifier: Mapped[str] = mapped_column(String(255), index=True)  # e.g. @groomer_handle, +919876543210
    identifier_type: Mapped[str] = mapped_column(String(50), default="SOCIAL_HANDLE")  # SOCIAL_HANDLE, PHONE_NUMBER, EMAIL, IP_ADDRESS, ONLINE_GAMING_TAG
    platform: Mapped[str] = mapped_column(String(50), default="OTHER")  # INSTAGRAM, TELEGRAM, WHATSAPP, DISCORD, SNAPCHAT, ROBLOX, OTHER
    risk_level: Mapped[str] = mapped_column(String(30), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active_threat: Mapped[bool] = mapped_column(Boolean, default=True)

class IncidentSuspectLink(Base, TimestampMixin):
    """
    Associates an Incident (or Case) with a SuspectEntity, detailing the specific Modus Operandi (MO).
    """
    __tablename__ = "incident_suspect_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    suspect_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suspect_entities.id", ondelete="CASCADE"), index=True)
    modus_operandi: Mapped[str] = mapped_column(String(100), default="UNKNOWN")  # GROOMING_GIFTING, SEXTORTION, COERCION_BULLYING, MEETUP_ENTICEMENT, IMPERSONATION, CYBERSTALKING
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
