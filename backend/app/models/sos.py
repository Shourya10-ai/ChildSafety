from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, Float, DateTime, text, Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator
from app.db.base import Base, TimestampMixin

class SafePointGeometry(TypeDecorator):
    """
    On PostgreSQL with PostGIS, uses Geometry('POINT', srid=4326).
    On SQLite or other dialects, falls back to Text, avoiding Spatialite binary requirements.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from geoalchemy2 import Geometry
                return dialect.type_descriptor(Geometry('POINT', srid=4326))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

class SOSEvent(Base, TimestampMixin):
    __tablename__ = "sos_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("children.id", ondelete="CASCADE"))
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    location = Column(SafePointGeometry(), nullable=True)
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")  # active, resolved, false_alarm
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
