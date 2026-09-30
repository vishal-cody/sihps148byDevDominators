"""JOCKY Collectors — System information collector (Windows + Linux)

Gathers hostname, OS, version, architecture, user, and hardware info.
Safe, read-only collection.
"""
from __future__ import annotations

import getpass
import os
import platform
from datetime import datetime
from typing import Any

from app.runtime.collectors.base import BaseCollector
from app.runtime.execution_context import ExecutionContext

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SystemCollector(BaseCollector):
    """Cross-platform system information collector."""

    name = "system"

    def collect(self, context: ExecutionContext, arguments: dict[str, Any] | None = None) -> list[dict]:
        boot_time = ""
        total_ram_gb = 0.0
        cpu_count = os.cpu_count() or 0
        cpu_model = ""

        if HAS_PSUTIL:
            try:
                boot_time = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            except Exception:
                boot_time = ""

            try:
                mem = psutil.virtual_memory()
                total_ram_gb = round(mem.total / (1024 ** 3), 2)
            except Exception:
                pass

        # CPU model — platform-specific
        try:
            if platform.system() == "Windows":
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                )
                cpu_model = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                winreg.CloseKey(key)
            else:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            cpu_model = line.split(":")[1].strip()
                            break
        except Exception:
            cpu_model = platform.processor() or "unknown"

        try:
            current_user = getpass.getuser()
        except Exception:
            current_user = "unknown"

        info = {
            "hostname": platform.node(),
            "os_type": platform.system().lower(),
            "os_version": platform.platform(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "cpu_model": cpu_model,
            "cpu_count": cpu_count,
            "total_ram_gb": total_ram_gb,
            "boot_time": boot_time,
            "current_user": current_user,
            "python_version": platform.python_version(),
            "agent_version": context.collector_version,
            "collected_at": datetime.utcnow().isoformat(),
        }

        context.add_log(f"System collector: {info['hostname']} ({info['os_type']} {info['os_release']})")
        return [info]


def get_system_collector(platform_name: str) -> SystemCollector | None:
    """Factory: return the system collector (cross-platform)."""
    return SystemCollector()
