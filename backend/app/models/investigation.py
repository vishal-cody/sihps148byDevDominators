"""JOCKY Platform — SQLAlchemy Models: Investigations & Executions"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    # created, running, completed, failed, cancelled
    priority: Mapped[str] = mapped_column(String(16), default="medium")  # low, medium, high, critical
    assigned_hosts: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list of host IDs
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    jocky_script_id: Mapped[str] = mapped_column(String(36), nullable=True)
    is_demo: Mapped[bool] = mapped_column(String(1), default="0")

    executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="investigation")


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), nullable=False)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending, dispatched, collecting, analyzing, completed, failed
    build_id: Mapped[str] = mapped_column(String(36), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    collection_stats: Mapped[str] = mapped_column(Text, nullable=True)  # JSON

    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="executions")
