"""JOCKY Platform — Evidence, Timeline, Findings API"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.evidence import ProcessRecord, NetworkConnection, PersistenceItem, EventLogRecord
from app.models.findings import Finding, TimelineEvent

router = APIRouter(prefix="/api", tags=["evidence"])


@router.get("/evidence/{investigation_id}/processes")
async def get_processes(
    investigation_id: str,
    host_id: Optional[str] = None,
    suspicious_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(ProcessRecord).where(ProcessRecord.investigation_id == investigation_id)
    if host_id:
        q = q.where(ProcessRecord.host_id == host_id)
    if suspicious_only:
        q = q.where(ProcessRecord.is_suspicious == True)
    q = q.order_by(ProcessRecord.collected_at.desc()).limit(500)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {"id": r.id, "host_id": r.host_id, "pid": r.pid, "ppid": r.ppid,
         "name": r.name, "path": r.path, "cmdline": r.cmdline,
         "username": r.username, "cpu_percent": r.cpu_percent,
         "memory_mb": r.memory_mb, "status": r.status,
         "created_time": r.created_time.isoformat() if r.created_time else None,
         "sha256_hash": r.sha256_hash, "is_suspicious": r.is_suspicious}
        for r in rows
    ]


@router.get("/evidence/{investigation_id}/network")
async def get_network(
    investigation_id: str,
    host_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(NetworkConnection).where(NetworkConnection.investigation_id == investigation_id)
    if host_id:
        q = q.where(NetworkConnection.host_id == host_id)
    q = q.order_by(NetworkConnection.collected_at.desc()).limit(500)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {"id": r.id, "host_id": r.host_id, "local_address": r.local_address,
         "local_port": r.local_port, "remote_address": r.remote_address,
         "remote_port": r.remote_port, "protocol": r.protocol,
         "state": r.state, "pid": r.pid, "process_name": r.process_name,
         "is_suspicious": r.is_suspicious}
        for r in rows
    ]


@router.get("/evidence/{investigation_id}/persistence")
async def get_persistence(
    investigation_id: str,
    host_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(PersistenceItem).where(PersistenceItem.investigation_id == investigation_id)
    if host_id:
        q = q.where(PersistenceItem.host_id == host_id)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {"id": r.id, "host_id": r.host_id, "category": r.category,
         "location": r.location, "name": r.name, "value": r.value,
         "command": r.command, "enabled": r.enabled,
         "created_time": r.created_time.isoformat() if r.created_time else None,
         "is_suspicious": r.is_suspicious}
        for r in rows
    ]


@router.get("/timeline/{investigation_id}")
async def get_timeline(
    investigation_id: str,
    host_id: Optional[str] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=200, le=1000),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(TimelineEvent).where(TimelineEvent.investigation_id == investigation_id)
    if host_id:
        q = q.where(TimelineEvent.host_id == host_id)
    if severity:
        q = q.where(TimelineEvent.severity == severity)
    if event_type:
        q = q.where(TimelineEvent.event_type == event_type)
    q = q.order_by(TimelineEvent.timestamp.asc()).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {"id": r.id, "host_id": r.host_id,
         "timestamp": r.timestamp.isoformat() if r.timestamp else None,
         "event_type": r.event_type, "severity": r.severity,
         "title": r.title, "description": r.description,
         "actor": r.actor, "target": r.target, "is_suspicious": r.is_suspicious}
        for r in rows
    ]


@router.get("/findings/{investigation_id}")
async def get_findings(
    investigation_id: str,
    severity: Optional[str] = None,
    host_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Finding).where(Finding.investigation_id == investigation_id)
    if severity:
        q = q.where(Finding.severity == severity)
    if host_id:
        q = q.where(Finding.host_id == host_id)
    q = q.order_by(Finding.severity.desc(), Finding.confidence.desc())
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {"id": r.id, "host_id": r.host_id, "title": r.title,
         "description": r.description, "severity": r.severity,
         "confidence": r.confidence, "category": r.category,
         "rule_id": r.rule_id, "mitre_technique": r.mitre_technique,
         "recommendation": r.recommendation, "status": r.status,
         "created_at": r.created_at.isoformat() if r.created_at else None,
         "evidence_refs": r.evidence_refs, "related_events": r.related_events}
        for r in rows
    ]


@router.get("/graph/{investigation_id}")
async def get_evidence_graph(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.services.graph_service import build_evidence_graph
    return await build_evidence_graph(investigation_id, db)
