"""JOCKY Collectors — Filesystem / File hash collector (Windows + Linux)

Computes SHA-256 hashes and gathers metadata for files.
Safe, read-only collection — no file modification.
"""
from __future__ import annotations

import hashlib
import os
import stat
from datetime import datetime
from typing import Any

from app.runtime.collectors.base import BaseCollector
from app.runtime.execution_context import ExecutionContext


# Default paths to scan for interesting artifacts
DEFAULT_SCAN_PATHS_WINDOWS = [
    os.path.expandvars(r"%TEMP%"),
    os.path.expandvars(r"%APPDATA%"),
    r"C:\ProgramData",
]

DEFAULT_SCAN_PATHS_LINUX = [
    "/tmp",
    "/var/tmp",
    "/home",
]


class FilesystemCollector(BaseCollector):
    """Cross-platform file metadata and hash collector."""

    name = "filesystem"

    def collect(self, context: ExecutionContext, arguments: dict[str, Any] | None = None) -> list[dict]:
        arguments = arguments or {}
        paths = arguments.get("paths", [])

        if not paths:
            # Use defaults based on platform
            if context.platform_name == "windows":
                paths = DEFAULT_SCAN_PATHS_WINDOWS
            else:
                paths = DEFAULT_SCAN_PATHS_LINUX

        results: list[dict] = []
        max_files = arguments.get("max_files", 500)
        count = 0

        for scan_path in paths:
            if not os.path.exists(scan_path):
                context.add_log(f"  Filesystem: path not found: {scan_path}")
                continue

            if os.path.isfile(scan_path):
                record = self._file_record(scan_path, context)
                if record:
                    results.append(record)
                    count += 1
                continue

            try:
                for dirpath, dirnames, filenames in os.walk(scan_path):
                    # Limit depth to avoid scanning entire filesystem
                    depth = dirpath.replace(scan_path, "").count(os.sep)
                    if depth > 2:
                        dirnames.clear()
                        continue

                    for fname in filenames:
                        if count >= max_files:
                            break
                        fpath = os.path.join(dirpath, fname)
                        record = self._file_record(fpath, context)
                        if record:
                            results.append(record)
                            count += 1

                    if count >= max_files:
                        break
            except PermissionError:
                continue

        context.add_log(f"Filesystem collector: {len(results)} files scanned")
        return results

    def _file_record(self, path: str, context: ExecutionContext) -> dict | None:
        """Build a file metadata record with SHA-256 hash."""
        try:
            st = os.stat(path)
        except (PermissionError, OSError, FileNotFoundError):
            return None

        # Compute SHA-256
        sha256 = ""
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            sha256 = h.hexdigest()
        except (PermissionError, OSError, IsADirectoryError):
            sha256 = ""

        try:
            owner = ""
            if context.platform_name != "windows":
                import pwd
                owner = pwd.getpwuid(st.st_uid).pw_name
        except Exception:
            owner = ""

        permissions = ""
        try:
            permissions = oct(stat.S_IMODE(st.st_mode))
        except Exception:
            pass

        return {
            "path": path,
            "size_bytes": st.st_size,
            "created_time": datetime.fromtimestamp(st.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(st.st_mtime).isoformat(),
            "accessed_time": datetime.fromtimestamp(st.st_atime).isoformat(),
            "sha256_hash": sha256,
            "owner": owner,
            "permissions": permissions,
        }


def get_filesystem_collector(platform_name: str) -> FilesystemCollector | None:
    """Factory: return the filesystem collector (cross-platform)."""
    return FilesystemCollector()
