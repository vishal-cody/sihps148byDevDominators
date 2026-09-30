"""JOCKY Platform — Timeline Service"""
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.findings import TimelineEvent
from app.models.evidence import ProcessRecord, NetworkConnection, PersistenceItem, EventLogRecord


async def build_timeline(investigation_id: str, host_id: str, db: AsyncSession) -> List[TimelineEvent]:
    """Merge all evidence sources into sorted timeline events."""
    events = []

    # Processes
    q = await db.execute(
        select(ProcessRecord).where(
            ProcessRecord.investigation_id == investigation_id,
            ProcessRecord.host_id == host_id,
        )
    )
    for proc in q.scalars().all():
        if proc.created_time:
            sev = "high" if proc.is_suspicious else "info"
            events.append(TimelineEvent(
                investigation_id=investigation_id,
                host_id=host_id,
                timestamp=proc.created_time,
                event_type="process_start",
                source_table="processes",
                source_id=proc.id,
                severity=sev,
                title=f"Process started: {proc.name}",
                description=f"PID {proc.pid} • {proc.path or 'unknown path'} • User: {proc.username}",
                actor=proc.name,
                target=proc.path,
                is_suspicious=proc.is_suspicious,
            ))

    # Network connections
    q = await db.execute(
        select(NetworkConnection).where(
            NetworkConnection.investigation_id == investigation_id,
            NetworkConnection.host_id == host_id,
        )
    )
    for conn in q.scalars().all():
        if conn.collected_at:
            sev = "critical" if conn.is_suspicious else "info"
            events.append(TimelineEvent(
                investigation_id=investigation_id,
                host_id=host_id,
                timestamp=conn.collected_at,
                event_type="network_connect",
                source_table="network_connections",
                source_id=conn.id,
                severity=sev,
                title=f"Network: {conn.process_name} → {conn.remote_address}:{conn.remote_port}",
                description=f"{conn.protocol} {conn.state} • {conn.local_address}:{conn.local_port} → {conn.remote_address}:{conn.remote_port}",
                actor=conn.process_name,
                target=f"{conn.remote_address}:{conn.remote_port}",
                is_suspicious=conn.is_suspicious,
            ))

    # Persistence
    q = await db.execute(
        select(PersistenceItem).where(
            PersistenceItem.investigation_id == investigation_id,
            PersistenceItem.host_id == host_id,
        )
    )
    for item in q.scalars().all():
        if item.created_time:
            sev = "high" if item.is_suspicious else "info"
            events.append(TimelineEvent(
                investigation_id=investigation_id,
                host_id=host_id,
                timestamp=item.created_time,
                event_type="persistence_created",
                source_table="persistence_items",
                source_id=item.id,
                severity=sev,
                title=f"Persistence: {item.category} — {item.name}",
                description=f"{item.location}\n{item.command}",
                actor=item.name,
                target=item.location,
                is_suspicious=item.is_suspicious,
            ))

    # Event logs
    q = await db.execute(
        select(EventLogRecord).where(
            EventLogRecord.investigation_id == investigation_id,
            EventLogRecord.host_id == host_id,
        )
    )
    for log in q.scalars().all():
        sev_map = {"info": "info", "warning": "warning", "error": "high", "critical": "critical", "high": "high"}
        sev = sev_map.get(log.severity, "info")
        events.append(TimelineEvent(
            investigation_id=investigation_id,
            host_id=host_id,
            timestamp=log.timestamp,
            event_type=log.event_type or "system_event",
            source_table="event_logs",
            source_id=log.id,
            severity=sev,
            title=f"[{log.source}] {log.event_type} (ID:{log.event_id})",
            description=log.message,
            actor=log.user_name,
            target=None,
            is_suspicious=(sev in ("high", "critical")),
        ))

    # Sort chronologically
    events.sort(key=lambda e: e.timestamp or datetime.min)
    return events
