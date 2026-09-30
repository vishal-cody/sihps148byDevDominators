"""JOCKY Platform — SQLAlchemy Models: Evidence (Processes, Network, etc.)"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class ProcessRecord(Base):
    __tablename__ = "processes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    investigation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    ppid: Mapped[int] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=True)
    cmdline: Mapped[str] = mapped_column(Text, nullable=True)
    username: Mapped[str] = mapped_column(String(128), nullable=True)
    cpu_percent: Mapped[float] = mapped_column(Float, nullable=True)
    memory_mb: Mapped[float] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    md5_hash: Mapped[str] = mapped_column(String(32), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NetworkConnection(Base):
    __tablename__ = "network_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    investigation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    local_address: Mapped[str] = mapped_column(String(64), nullable=True)
    local_port: Mapped[int] = mapped_column(Integer, nullable=True)
    remote_address: Mapped[str] = mapped_column(String(64), nullable=True)
    remote_port: Mapped[int] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str] = mapped_column(String(8), nullable=True)
    state: Mapped[str] = mapped_column(String(32), nullable=True)
    pid: Mapped[int] = mapped_column(Integer, nullable=True)
    process_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PersistenceItem(Base):
    __tablename__ = "persistence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    investigation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    # registry_run, scheduled_task, service, startup_folder, cron, systemd
    location: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    value: Mapped[str] = mapped_column(Text, nullable=True)
    command: Mapped[str] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EventLogRecord(Base):
    __tablename__ = "event_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    investigation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=True)
    event_id: Mapped[int] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=True)  # info, warning, error, critical
    message: Mapped[str] = mapped_column(Text, nullable=True)
    process_id: Mapped[int] = mapped_column(Integer, nullable=True)
    user_name: Mapped[str] = mapped_column(String(128), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FilesystemEvent(Base):
    __tablename__ = "filesystem_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("executions.id"), nullable=False, index=True)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    investigation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=True)  # created, modified, deleted, accessed
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=True)
    permissions: Mapped[str] = mapped_column(String(32), nullable=True)
    md5_hash: Mapped[str] = mapped_column(String(32), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    event_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
