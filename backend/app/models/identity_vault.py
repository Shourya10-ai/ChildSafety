from __future__ import annotations
import uuid
from sqlalchemy import String, LargeBinary, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class IdentityVault(Base, TimestampMixin):
    __tablename__ = "identity_vaults"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    protected_child_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    encrypted_name: Mapped[bytes] = mapped_column(LargeBinary)
    encrypted_phone: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    encrypted_address: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    encrypted_school: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    encrypted_guardian_info: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    encryption_key_id: Mapped[str] = mapped_column(String(100))
