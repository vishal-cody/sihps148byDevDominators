"""JOCKY Collectors — Process collector (Windows + Linux)

Uses psutil for cross-platform process enumeration.
Safe, read-only collection of running process metadata.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime
from typing import Any

from agent.runtime.collectors.base import BaseCollector
from agent.runtime.execution_context import ExecutionContext

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class ProcessCollector(BaseCollector):
    """Cross-platform process collector using psutil."""

    name = "process"

    def collect(self, context: ExecutionContext, arguments: dict[str, Any] | None = None) -> list[dict]:
        if not HAS_PSUTIL:
            context.add_error("psutil not available — cannot collect processes")
            return []

        results: list[dict] = []

        for proc in psutil.process_iter([
            "pid", "ppid", "name", "exe", "cmdline", "username",
            "cpu_percent", "memory_info", "create_time", "status",
        ]):
            try:
                info = proc.info
                exe_path = info.get("exe") or ""
                exe_hash = ""
                if exe_path and os.path.isfile(exe_path):
                    try:
                        with open(exe_path, "rb") as f:
                            # Read first 64KB for fast hash (full hash is expensive)
                            exe_hash = hashlib.sha256(f.read(65536)).hexdigest()
                    except (PermissionError, OSError):
                        exe_hash = ""

                mem_info = info.get("memory_info")
                memory_mb = round(mem_info.rss / (1024 * 1024), 2) if mem_info else 0.0

                cmdline_raw = info.get("cmdline") or []
                cmdline_str = " ".join(cmdline_raw) if isinstance(cmdline_raw, list) else str(cmdline_raw)

                create_time = info.get("create_time")
                created_at = ""
                if create_time:
                    try:
                        created_at = datetime.fromtimestamp(create_time).isoformat()
                    except (OSError, ValueError):
                        created_at = ""

                results.append({
                    "pid": info.get("pid", 0),
                    "ppid": info.get("ppid", 0),
                    "name": info.get("name", ""),
                    "path": exe_path,
                    "cmdline": cmdline_str,
                    "username": info.get("username", ""),
                    "cpu_percent": info.get("cpu_percent", 0.0),
                    "memory_mb": memory_mb,
                    "status": info.get("status", ""),
                    "created_time": created_at,
                    "exe_hash_sha256": exe_hash,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        context.add_log(f"Process collector: {len(results)} processes enumerated")
        return results


def get_process_collector(platform_name: str) -> ProcessCollector | None:
    """Factory: return the process collector (cross-platform via psutil)."""
    if HAS_PSUTIL:
        return ProcessCollector()
    return None
