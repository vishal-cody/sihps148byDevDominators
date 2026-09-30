"""JOCKY Platform — Report Generator Service"""
import json
import os
import csv
from datetime import datetime
from typing import Optional

from app.database import AsyncSessionLocal
from app.config import get_settings
from app.models.findings import Report, Finding, TimelineEvent
from app.models.investigation import Investigation
from app.models.evidence import ProcessRecord, NetworkConnection, PersistenceItem
from app.models.host import Host

settings = get_settings()


async def generate_report_task(report_id: str, investigation_id: str, fmt: str):
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # Gather all data
        inv_q = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
        inv = inv_q.scalar_one_or_none()

        findings_q = await db.execute(select(Finding).where(Finding.investigation_id == investigation_id))
        findings = findings_q.scalars().all()

        timeline_q = await db.execute(
            select(TimelineEvent).where(TimelineEvent.investigation_id == investigation_id)
            .order_by(TimelineEvent.timestamp)
        )
        timeline = timeline_q.scalars().all()

        procs_q = await db.execute(select(ProcessRecord).where(ProcessRecord.investigation_id == investigation_id))
        processes = procs_q.scalars().all()

        network_q = await db.execute(select(NetworkConnection).where(NetworkConnection.investigation_id == investigation_id))
        network = network_q.scalars().all()

        persist_q = await db.execute(select(PersistenceItem).where(PersistenceItem.investigation_id == investigation_id))
        persistence = persist_q.scalars().all()

        os.makedirs(settings.report_output_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        case_id = inv.case_id if inv else investigation_id[:8]
        filename = f"JOCKY_Report_{case_id}_{timestamp}.{fmt}"
        filepath = os.path.join(settings.report_output_dir, filename)

        report_data = _build_report_data(inv, findings, timeline, processes, network, persistence)

        if fmt == "json":
            _export_json(report_data, filepath)
        elif fmt == "csv":
            _export_csv(findings, timeline, filepath)
        else:
            _export_json(report_data, filepath + ".json")
            filepath = filepath + ".json"

        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

        # Update report record
        report_q = await db.execute(select(Report).where(Report.id == report_id))
        report = report_q.scalar_one_or_none()
        if report:
            report.status = "completed"
            report.file_path = filepath
            report.filename = os.path.basename(filepath)
            report.file_size_bytes = file_size
            await db.commit()


def _build_report_data(inv, findings, timeline, processes, network, persistence):
    severity_counts = {}
    for f in findings:
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

    return {
        "report_metadata": {
            "title": f"JOCKY Forensic Investigation Report",
            "case_id": inv.case_id if inv else "N/A",
            "investigation_name": inv.name if inv else "N/A",
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": "JOCKY Platform v1.0.0",
            "classification": "FORENSIC EVIDENCE — CONTROLLED DOCUMENT",
        },
        "executive_summary": {
            "description": f"This report summarizes the forensic investigation '{inv.name if inv else 'N/A'}' conducted using the JOCKY forensic platform.",
            "total_findings": len(findings),
            "severity_breakdown": severity_counts,
            "high_risk_hosts": len(set(f.host_id for f in findings if f.severity in ("high", "critical"))),
            "timeline_events": len(timeline),
            "processes_analyzed": len(processes),
            "network_connections": len(network),
            "persistence_items": len(persistence),
        },
        "findings": [
            {
                "id": f.id, "title": f.title, "severity": f.severity,
                "confidence": f.confidence, "category": f.category,
                "description": f.description, "host_id": f.host_id,
                "mitre_technique": f.mitre_technique,
                "recommendation": f.recommendation,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in sorted(findings, key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity, 4))
        ],
        "timeline": [
            {
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "event_type": e.event_type, "severity": e.severity,
                "title": e.title, "description": e.description,
                "host_id": e.host_id, "actor": e.actor, "target": e.target,
                "is_suspicious": e.is_suspicious,
            }
            for e in timeline
        ],
        "processes": [
            {"name": p.name, "pid": p.pid, "ppid": p.ppid, "path": p.path,
             "username": p.username, "cpu_percent": p.cpu_percent,
             "memory_mb": p.memory_mb, "is_suspicious": p.is_suspicious,
             "host_id": p.host_id}
            for p in processes
        ],
        "network": [
            {"remote_address": n.remote_address, "remote_port": n.remote_port,
             "protocol": n.protocol, "state": n.state, "process_name": n.process_name,
             "is_suspicious": n.is_suspicious, "host_id": n.host_id}
            for n in network
        ],
        "persistence": [
            {"category": p.category, "name": p.name, "location": p.location,
             "command": p.command, "is_suspicious": p.is_suspicious,
             "host_id": p.host_id}
            for p in persistence
        ],
        "recommendations": _generate_recommendations(findings),
        "disclaimer": "This report was generated by the JOCKY forensic platform for authorized investigation purposes only. All high-risk capabilities in this platform are simulated. No real security control bypass was performed.",
    }


def _generate_recommendations(findings):
    recs = []
    has_persistence = any(f.category == "persistence" for f in findings)
    has_c2 = any("C2" in (f.description or "") or "4444" in (f.description or "") for f in findings)
    has_suspicious_proc = any(f.category == "process" and f.severity in ("high", "critical") for f in findings)

    if has_persistence:
        recs.append("Immediately audit and remove suspicious persistence mechanisms identified in findings.")
    if has_c2:
        recs.append("Block identified C2 IP addresses at firewall level and investigate lateral movement.")
    if has_suspicious_proc:
        recs.append("Terminate suspicious processes and collect memory dump for deep forensic analysis.")
    recs.append("Conduct full endpoint reimaging for hosts with critical findings.")
    recs.append("Enable enhanced logging (Sysmon + Windows Event Forwarding) across fleet.")
    return recs


def _export_json(data: dict, filepath: str):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _export_csv(findings, timeline, filepath: str):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Severity", "Title", "Description", "Host", "Timestamp"])
        for finding in findings:
            writer.writerow([
                "Finding", finding.severity, finding.title,
                finding.description, finding.host_id,
                finding.created_at.isoformat() if finding.created_at else ""
            ])
        for event in timeline:
            writer.writerow([
                "Timeline", event.severity, event.title,
                event.description, event.host_id,
                event.timestamp.isoformat() if event.timestamp else ""
            ])
