"""JOCKY Runtime — Execution Context

Holds all state needed during a single IR execution: case metadata,
collected evidence, execution log, platform info.
"""
import platform
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExecutionContext:
    """Mutable context passed to every collector and operation handler."""

    # ── Identity ──────────────────────────────────────────────────
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str = ""
    investigation_id: str = ""
    host_id: str = ""
    build_id: str = ""
    script_hash: str = ""

    # ── Platform ──────────────────────────────────────────────────
    platform_name: str = field(default_factory=lambda: platform.system().lower())  # "windows" | "linux"
    hostname: str = field(default_factory=platform.node)
    os_version: str = field(default_factory=platform.platform)
    architecture: str = field(default_factory=platform.machine)

    # ── Timing ────────────────────────────────────────────────────
    started_at: str = ""
    completed_at: str = ""

    # ── Results ───────────────────────────────────────────────────
    evidence: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    timeline_events: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    log: list[str] = field(default_factory=list)

    # ── Capabilities granted by policy ────────────────────────────
    granted_capabilities: set[str] = field(default_factory=set)

    # ── Config ────────────────────────────────────────────────────
    mode: str = "live"  # "live" | "demo"
    collector_version: str = "1.0.0"

    def add_evidence(self, evidence_type: str, collector: str, payload: dict) -> dict:
        """Add a normalized evidence record."""
        record = {
            "evidence_id": str(uuid.uuid4()),
            "case_id": self.case_id,
            "execution_id": self.execution_id,
            "host_id": self.host_id,
            "collector": collector,
            "collector_version": self.collector_version,
            "platform": self.platform_name,
            "type": evidence_type,
            "collected_at": datetime.utcnow().isoformat(),
            "payload": payload,
        }
        self.evidence.append(record)
        return record

    def add_log(self, message: str):
        ts = datetime.utcnow().isoformat()
        entry = f"[{ts}] {message}"
        self.log.append(entry)

    def add_error(self, message: str):
        self.errors.append(message)
        self.add_log(f"ERROR: {message}")

    def start(self):
        self.started_at = datetime.utcnow().isoformat()
        self.add_log("Execution started")

    def finish(self):
        self.completed_at = datetime.utcnow().isoformat()
        self.add_log(f"Execution completed — {len(self.evidence)} evidence items, {len(self.errors)} errors")

    def to_result(self) -> dict:
        """Serialize the full execution result for upload to the backend."""
        return {
            "execution_id": self.execution_id,
            "case_id": self.case_id,
            "investigation_id": self.investigation_id,
            "host_id": self.host_id,
            "build_id": self.build_id,
            "script_hash": self.script_hash,
            "platform": self.platform_name,
            "hostname": self.hostname,
            "os_version": self.os_version,
            "architecture": self.architecture,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "mode": self.mode,
            "evidence": self.evidence,
            "findings": self.findings,
            "timeline_events": self.timeline_events,
            "errors": self.errors,
            "log": self.log,
            "stats": {
                "total_evidence": len(self.evidence),
                "total_errors": len(self.errors),
                "evidence_by_type": self._count_by("type"),
            },
        }

    def _count_by(self, key: str) -> dict:
        counts: dict[str, int] = {}
        for e in self.evidence:
            val = e.get(key, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts
