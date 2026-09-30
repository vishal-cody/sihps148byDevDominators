"""JOCKY Platform — SQLAlchemy Models: JOCKY Scripts & Builds"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class JockyScript(Base):
    __tablename__ = "jocky_scripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_valid: Mapped[bool] = mapped_column(String(1), default="1")
    last_compiled: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_build_id: Mapped[str] = mapped_column(String(36), nullable=True)


class JockyBuild(Base):
    __tablename__ = "jocky_builds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    script_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    build_number: Mapped[int] = mapped_column(Integer, default=1)
    profile: Mapped[str] = mapped_column(String(32), default="forensic_standard")
    # forensic_standard, forensic_hardened, forensic_variant
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    ir_json: Mapped[str] = mapped_column(Text, nullable=True)  # full IR JSON
    ir_node_count: Mapped[int] = mapped_column(Integer, default=0)
    transformation_log: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list
    build_metadata: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    build_time_ms: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(32), default="success")
