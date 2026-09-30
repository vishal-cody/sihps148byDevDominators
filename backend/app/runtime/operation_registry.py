"""JOCKY Runtime — Operation Registry

Maps IR opcodes to handler functions. Collectors are registered as
platform-specific implementations.
"""
from __future__ import annotations

import platform
from typing import Any, Callable, Protocol

from app.runtime.execution_context import ExecutionContext


# ── Collector Protocol ────────────────────────────────────────────

class Collector(Protocol):
    """Interface that every platform-specific collector must satisfy."""

    def collect(self, context: ExecutionContext, arguments: dict[str, Any] | None = None) -> list[dict]:
        """Collect evidence and return list of payload dicts."""
        ...


# ── Registry ──────────────────────────────────────────────────────

_collectors: dict[str, dict[str, Collector]] = {}
# Structure: { "PROCESSES": { "windows": WindowsProcessCollector(), "linux": LinuxProcessCollector() } }


def register_collector(target: str, platform_name: str, collector: Collector):
    """Register a collector for a specific target and platform."""
    if target not in _collectors:
        _collectors[target] = {}
    _collectors[target][platform_name] = collector


def get_collector(target: str, platform_name: str | None = None) -> Collector | None:
    """Get the appropriate collector for this target and platform."""
    if platform_name is None:
        platform_name = platform.system().lower()
    return _collectors.get(target, {}).get(platform_name)


def get_available_targets() -> list[str]:
    """Return all registered collector targets."""
    return list(_collectors.keys())


def get_available_collectors(platform_name: str | None = None) -> dict[str, bool]:
    """Return target → available mapping for the specified platform."""
    if platform_name is None:
        platform_name = platform.system().lower()
    return {
        target: platform_name in platforms
        for target, platforms in _collectors.items()
    }


# ── Auto-registration ────────────────────────────────────────────

def register_all_collectors():
    """Import and register all platform collectors."""
    current_platform = platform.system().lower()

    # Always register cross-platform collectors
    from app.runtime.collectors.process import get_process_collector
    from app.runtime.collectors.network import get_network_collector
    from app.runtime.collectors.system import get_system_collector
    from app.runtime.collectors.filesystem import get_filesystem_collector

    proc_collector = get_process_collector(current_platform)
    if proc_collector:
        register_collector("PROCESSES", current_platform, proc_collector)

    net_collector = get_network_collector(current_platform)
    if net_collector:
        register_collector("NETWORK_CONNECTIONS", current_platform, net_collector)

    sys_collector = get_system_collector(current_platform)
    if sys_collector:
        register_collector("SYSTEM_INFO", current_platform, sys_collector)

    fs_collector = get_filesystem_collector(current_platform)
    if fs_collector:
        register_collector("FILE_HASH", current_platform, fs_collector)
        register_collector("FILESYSTEM", current_platform, fs_collector)
