from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, ForeignKey, Text, DateTime, text, Column
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from app.db.base import Base, TimestampMixin

class MissingChild(Base, TimestampMixin):
    __tablename__ = "missing_children"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"))
    child_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("children.id", ondelete="SET NULL"), nullable=True)
    photo_url: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    age_when_missing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    clothing_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    identifying_marks: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_known_location = Column(Geometry('POINT', srid=4326), nullable=True)
    last_known_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30))
    photo_embedding = Column(Vector(512), nullable=True)

class CCTVCandidate(Base, TimestampMixin):
    __tablename__ = "cctv_candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    missing_child_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("missing_children.id", ondelete="CASCADE"))
    image_url: Mapped[str] = mapped_column(String(500))
    similarity_score: Mapped[float] = mapped_column(Float)
    location = Column(Geometry('POINT', srid=4326), nullable=True)
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    embedding = Column(Vector(512), nullable=True)
