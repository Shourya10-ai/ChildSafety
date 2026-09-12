from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class EvidenceChainOfCustody(Base):
    """
    Immutable, Cryptographically Linked Chain of Custody Ledger:
    Compliant with Section 63 of Bharatiya Sakshya Adhiniyam, 2023 (formerly Sec 65B IEA).
    Each entry is chained to the previous block via SHA-256 and signed with HMAC-SHA256,
    making database alterations mathematically evident.
    """
    __tablename__ = "evidence_chain_of_custody"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidences.id", ondelete="CASCADE"),
        index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(50))  # UPLOADED, AI_ANALYZED, ACCESSED, VERIFIED, EXPORTED
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    actor_role: Mapped[str] = mapped_column(String(30))
    file_sha256: Mapped[str] = mapped_column(String(64))
    previous_block_hash: Mapped[str] = mapped_column(String(64))
    entry_payload_hash: Mapped[str] = mapped_column(String(64))
    block_hash: Mapped[str] = mapped_column(String(64), index=True)
    digital_signature: Mapped[str] = mapped_column(String(128))
    metadata_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
