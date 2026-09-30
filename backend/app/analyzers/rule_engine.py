"""JOCKY Platform — Rule-Based Analytics Engine"""
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.evidence import ProcessRecord, NetworkConnection, PersistenceItem, EventLogRecord
from app.models.findings import Finding


RULES = [
    {
        "id": "PROC-001",
        "name": "Process in Temp Directory",
        "category": "process",
        "severity": "high",
        "confidence": 0.87,
        "mitre": "T1204.002",
        "description": "Executable running from a user-writable temp location.",
        "recommendation": "Investigate the process origin, check parent process chain, and terminate if unauthorized.",
    },
    {
        "id": "PROC-002",
        "name": "Typosquatted System Process",
        "category": "process",
        "severity": "critical",
        "confidence": 0.94,
        "mitre": "T1036.004",
        "description": "Process name closely resembles a legitimate Windows system process (possible masquerading).",
        "recommendation": "Immediately terminate, collect memory dump, and block hash at EDR level.",
    },
    {
        "id": "NET-001",
        "name": "Connection to High-Risk Port",
        "category": "network",
        "severity": "critical",
        "confidence": 0.91,
        "mitre": "T1071.001",
        "description": "Outbound connection to uncommon port (4444, 1337, 8888, etc.) associated with C2 frameworks.",
        "recommendation": "Block IP at firewall, investigate process responsible, check for lateral movement.",
    },
    {
        "id": "NET-002",
        "name": "Connection to Known Threat Actor IP Range",
        "category": "network",
        "severity": "critical",
        "confidence": 0.89,
        "mitre": "T1071.001",
        "description": "Network connection to IP range associated with known threat infrastructure (185.220.x.x Tor exit range).",
        "recommendation": "Block subnet, initiate incident response, preserve network logs.",
    },
    {
        "id": "PERSIST-001",
        "name": "Suspicious Registry Run Key",
        "category": "persistence",
        "severity": "high",
        "confidence": 0.86,
        "mitre": "T1547.001",
        "description": "Run key added in HKCU pointing to executable in non-standard location.",
        "recommendation": "Remove registry key, quarantine the binary, and investigate origin.",
    },
    {
        "id": "PERSIST-002",
        "name": "Suspicious Scheduled Task",
        "category": "persistence",
        "severity": "high",
        "confidence": 0.83,
        "mitre": "T1053.005",
        "description": "Scheduled task created pointing to executable in ProgramData or Temp.",
        "recommendation": "Delete scheduled task, quarantine associated binary.",
    },
    {
        "id": "PROC-003",
        "name": "High CPU Suspicious Process",
        "category": "process",
        "severity": "medium",
        "confidence": 0.72,
        "mitre": "T1496",
        "description": "Suspicious process consuming unusually high CPU (possible cryptominer or beaconing).",
        "recommendation": "Investigate process activity, check network connections from this PID.",
    },
]


def _is_temp_path(path: str) -> bool:
    if not path:
        return False
    path_lower = path.lower()
    return any(x in path_lower for x in ["\\temp\\", "\\tmp\\", "\\appdata\\local\\temp\\", "/tmp/"])


def _is_typosquat(name: str) -> bool:
    legit = {"svchost.exe", "lsass.exe", "csrss.exe", "winlogon.exe", "services.exe", "explorer.exe"}
    name_lower = name.lower()
    return any(
        name_lower != l and (
            name_lower.replace("0", "o") == l or
            name_lower.replace("1", "l") == l or
            name_lower.replace("l", "1") == l or
            (len(name_lower) == len(l) and sum(a != b for a, b in zip(name_lower, l)) == 1)
        )
        for l in legit
    )


def _is_c2_port(port) -> bool:
    if not port:
        return False
    return port in (4444, 1337, 8888, 6666, 9999, 31337, 4545, 8443, 2222)


def _is_tor_exit(ip: str) -> bool:
    if not ip:
        return False
    return ip.startswith("185.220.") or ip.startswith("185.100.") or ip.startswith("51.77.")


async def run_rules(investigation_id: str, host_id: str, db: AsyncSession) -> List[Finding]:
    findings = []

    # Process rules
    pq = await db.execute(
        select(ProcessRecord).where(
            ProcessRecord.investigation_id == investigation_id,
            ProcessRecord.host_id == host_id,
        )
    )
    for proc in pq.scalars().all():
        if _is_temp_path(proc.path or ""):
            rule = next(r for r in RULES if r["id"] == "PROC-001")
            findings.append(Finding(
                investigation_id=investigation_id, host_id=host_id,
                title=rule["name"],
                description=f"{rule['description']}\n\nProcess: {proc.name} (PID:{proc.pid})\nPath: {proc.path}",
                severity=rule["severity"], confidence=rule["confidence"],
                category=rule["category"], rule_id=rule["id"],
                mitre_technique=rule["mitre"],
                recommendation=rule["recommendation"],
                evidence_refs=f'[{{"type":"process","id":"{proc.id}"}}]',
            ))

        if _is_typosquat(proc.name):
            rule = next(r for r in RULES if r["id"] == "PROC-002")
            findings.append(Finding(
                investigation_id=investigation_id, host_id=host_id,
                title=rule["name"],
                description=f"{rule['description']}\n\nProcess: '{proc.name}' (PID:{proc.pid}) — resembles legitimate system process.",
                severity=rule["severity"], confidence=rule["confidence"],
                category=rule["category"], rule_id=rule["id"],
                mitre_technique=rule["mitre"],
                recommendation=rule["recommendation"],
                evidence_refs=f'[{{"type":"process","id":"{proc.id}"}}]',
            ))

        if proc.is_suspicious and (proc.cpu_percent or 0) > 10:
            rule = next(r for r in RULES if r["id"] == "PROC-003")
            findings.append(Finding(
                investigation_id=investigation_id, host_id=host_id,
                title=rule["name"],
                description=f"{rule['description']}\n\nProcess: {proc.name} using {proc.cpu_percent}% CPU",
                severity=rule["severity"], confidence=rule["confidence"],
                category=rule["category"], rule_id=rule["id"],
                mitre_technique=rule["mitre"],
                recommendation=rule["recommendation"],
            ))

    # Network rules
    nq = await db.execute(
        select(NetworkConnection).where(
            NetworkConnection.investigation_id == investigation_id,
            NetworkConnection.host_id == host_id,
        )
    )
    for conn in nq.scalars().all():
        if _is_c2_port(conn.remote_port):
            rule = next(r for r in RULES if r["id"] == "NET-001")
            findings.append(Finding(
                investigation_id=investigation_id, host_id=host_id,
                title=rule["name"],
                description=f"{rule['description']}\n\nConnection: {conn.local_address} → {conn.remote_address}:{conn.remote_port} via {conn.process_name}",
                severity=rule["severity"], confidence=rule["confidence"],
                category=rule["category"], rule_id=rule["id"],
                mitre_technique=rule["mitre"],
                recommendation=rule["recommendation"],
                evidence_refs=f'[{{"type":"network","id":"{conn.id}"}}]',
            ))

        if _is_tor_exit(conn.remote_address or ""):
            rule = next(r for r in RULES if r["id"] == "NET-002")
            findings.append(Finding(
                investigation_id=investigation_id, host_id=host_id,
                title=rule["name"],
                description=f"{rule['description']}\n\nIP: {conn.remote_address} via {conn.process_name or 'unknown process'}",
                severity=rule["severity"], confidence=rule["confidence"],
                category=rule["category"], rule_id=rule["id"],
                mitre_technique=rule["mitre"],
                recommendation=rule["recommendation"],
                evidence_refs=f'[{{"type":"network","id":"{conn.id}"}}]',
            ))

    # Persistence rules
    peq = await db.execute(
        select(PersistenceItem).where(
            PersistenceItem.investigation_id == investigation_id,
            PersistenceItem.host_id == host_id,
            PersistenceItem.is_suspicious == True,
        )
    )
    for item in peq.scalars().all():
        rule_id = "PERSIST-001" if "registry" in item.category else "PERSIST-002"
        rule = next(r for r in RULES if r["id"] == rule_id)
        findings.append(Finding(
            investigation_id=investigation_id, host_id=host_id,
            title=rule["name"],
            description=f"{rule['description']}\n\nLocation: {item.location}\nCommand: {item.command}",
            severity=rule["severity"], confidence=rule["confidence"],
            category=rule["category"], rule_id=rule["id"],
            mitre_technique=rule["mitre"],
            recommendation=rule["recommendation"],
            evidence_refs=f'[{{"type":"persistence","id":"{item.id}"}}]',
        ))

    return findings
