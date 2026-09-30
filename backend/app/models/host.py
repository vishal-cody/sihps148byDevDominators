"""JOCKY Platform — SQLAlchemy Models: Hosts & Agents"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)
    os_type: Mapped[str] = mapped_column(String(64), nullable=True)  # windows, linux, macos
    os_version: Mapped[str] = mapped_column(String(128), nullable=True)
    architecture: Mapped[str] = mapped_column(String(32), nullable=True)
    cpu_model: Mapped[str] = mapped_column(String(255), nullable=True)
    ram_gb: Mapped[float] = mapped_column(Float, nullable=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=True)
    agent_version: Mapped[str] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="offline")  # online, offline, investigating
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list

    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="host")


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    host_id: Mapped[str] = mapped_column(String(36), ForeignKey("hosts.id"), nullable=False, index=True)
    agent_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="idle")  # idle, busy, error
    last_heartbeat: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    capabilities: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list

    host: Mapped["Host"] = relationship("Host", back_populates="agents")
