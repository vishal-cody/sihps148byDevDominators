"""JOCKY Platform — SQLAlchemy Models: Findings, Timelines, Indicators"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), nullable=False, index=True)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)  # low, medium, high, critical
    confidence: Mapped[float] = mapped_column(Float, default=0.7)
    category: Mapped[str] = mapped_column(String(64), nullable=True)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=True)
    evidence_refs: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list of evidence IDs/types
    related_events: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    mitre_technique: Mapped[str] = mapped_column(String(32), nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")  # open, acknowledged, resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), nullable=False, index=True)
    host_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # process_start, process_stop, network_connect, network_disconnect,
    # persistence_created, file_created, file_modified, auth_event, system_event
    source_table: Mapped[str] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), default="info")
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=True)  # process/user
    target: Mapped[str] = mapped_column(String(255), nullable=True)  # file/IP/etc
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    indicator_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # ip, domain, file_hash, process_name, registry_key, url
    value: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    is_ioc: Mapped[bool] = mapped_column(Boolean, default=False)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    investigation_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigations.id"), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(16), nullable=False)  # pdf, json, csv
    filename: Mapped[str] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(36), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(32), default="generating")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)
