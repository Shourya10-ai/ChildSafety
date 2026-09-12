from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime, text, Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator
from app.db.base import Base, TimestampMixin

class SafePointGeometry(TypeDecorator):
    """
    On PostgreSQL with PostGIS, uses Geometry('POINT', srid=4326).
    On SQLite or other dialects, falls back to Text, avoiding Spatialite requirements.
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

class SafeVector(TypeDecorator):
    """
    On PostgreSQL with pgvector, uses Vector(512).
    On SQLite, falls back to Text.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(512))
            except ImportError:
                return dialect.type_descriptor(Text())
        return dialect.type_descriptor(Text())

class MissingChild(Base, TimestampMixin):
    __tablename__ = "missing_children"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    child_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("children.id", ondelete="SET NULL"), nullable=True)
    child_name: Mapped[str] = mapped_column(String(200))
    photo_url: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    age_when_missing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    clothing_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    identifying_marks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    last_known_location = Column(SafePointGeometry, nullable=True)
    last_known_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")  # ACTIVE, FOUND, CLOSED
    reported_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    photo_embedding = Column(SafeVector, nullable=True)

class CCTVCandidate(Base, TimestampMixin):
    __tablename__ = "cctv_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    missing_child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("missing_children.id", ondelete="CASCADE"))
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    similarity_score: Mapped[float | None] = mapped_column(Float, default=0.0)
    
    location = Column(SafePointGeometry, nullable=True)
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="CITIZEN_SIGHTING")  # CITIZEN_SIGHTING, LIGHTWEIGHT_CCTV
    sighting_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reported_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(30), default="PENDING_REVIEW")  # PENDING_REVIEW, VERIFIED_MATCH, DISMISSED
    verified_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    embedding = Column(SafeVector, nullable=True)
