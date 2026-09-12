from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, Text, DateTime, text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin

class Moderator(Base, TimestampMixin):
    __tablename__ = "moderators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    employee_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active_case_count: Mapped[int] = mapped_column(Integer, default=0)
    max_cases: Mapped[int] = mapped_column(Integer, default=20)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"))
    moderator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("moderators.id", ondelete="CASCADE"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
