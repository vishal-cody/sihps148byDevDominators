"""JOCKY Platform — SQLAlchemy Models: Provenance and Integrity"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class EvidenceManifest(Base):
    __tablename__ = "evidence_manifests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    evidence_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    script_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    build_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    
    collector_version: Mapped[str] = mapped_column(String(32), nullable=True)
    evidence_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
