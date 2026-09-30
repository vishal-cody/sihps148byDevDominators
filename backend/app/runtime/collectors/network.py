"""JOCKY Collectors — Network connection collector (Windows + Linux)

Uses psutil for cross-platform network connection enumeration.
Safe, read-only collection of active network connections.
"""
from __future__ import annotations

from typing import Any

from app.runtime.collectors.base import BaseCollector
from app.runtime.execution_context import ExecutionContext

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class NetworkCollector(BaseCollector):
    """Cross-platform network connection collector using psutil."""

    name = "network"

    def collect(self, context: ExecutionContext, arguments: dict[str, Any] | None = None) -> list[dict]:
        if not HAS_PSUTIL:
            context.add_error("psutil not available — cannot collect network connections")
            return []

        results: list[dict] = []

        try:
            connections = psutil.net_connections(kind="all")
        except (psutil.AccessDenied, PermissionError):
            context.add_error("Insufficient permissions for network collection (try running as admin/root)")
            return []

        # Build PID → process name map
        pid_name_map: dict[int, str] = {}
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pid_name_map[proc.info["pid"]] = proc.info["name"]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        for conn in connections:
            local_addr = ""
            local_port = 0
            remote_addr = ""
            remote_port = 0

            if conn.laddr:
                local_addr = conn.laddr.ip if hasattr(conn.laddr, "ip") else str(conn.laddr[0])
                local_port = conn.laddr.port if hasattr(conn.laddr, "port") else int(conn.laddr[1])

            if conn.raddr:
                remote_addr = conn.raddr.ip if hasattr(conn.raddr, "ip") else str(conn.raddr[0])
                remote_port = conn.raddr.port if hasattr(conn.raddr, "port") else int(conn.raddr[1])

            # Map protocol numbers
            proto_map = {1: "ICMP", 6: "TCP", 17: "UDP"}
            proto_type = conn.type if hasattr(conn, "type") else 0
            protocol = proto_map.get(proto_type, str(proto_type))

            # psutil uses socket type enums
            if hasattr(conn, "type"):
                import socket
                if conn.type == socket.SOCK_STREAM:
                    protocol = "TCP"
                elif conn.type == socket.SOCK_DGRAM:
                    protocol = "UDP"

            pid = conn.pid or 0
            process_name = pid_name_map.get(pid, "")

            results.append({
                "local_address": local_addr,
                "local_port": local_port,
                "remote_address": remote_addr,
                "remote_port": remote_port,
                "protocol": protocol,
                "state": conn.status if hasattr(conn, "status") else "",
                "pid": pid,
                "process_name": process_name,
            })

        context.add_log(f"Network collector: {len(results)} connections enumerated")
        return results


def get_network_collector(platform_name: str) -> NetworkCollector | None:
    """Factory: return the network collector (cross-platform via psutil)."""
    if HAS_PSUTIL:
        return NetworkCollector()
    return None
