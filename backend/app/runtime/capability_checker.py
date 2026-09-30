"""JOCKY Runtime — Capability Checker

Validates that the host / policy allows all capabilities required by the IR.
"""
from typing import Any

from app.runtime.errors import PolicyDeniedError, CapabilityError


# ── Capability definitions ────────────────────────────────────────
CAPABILITY_MAP: dict[str, list[str]] = {
    "PROCESSES":            ["PROCESS_READ"],
    "NETWORK_CONNECTIONS":  ["NETWORK_READ"],
    "SYSTEM_INFO":          ["SYSTEM_INFO_READ"],
    "FILE_HASH":            ["FILE_READ", "FILE_HASH"],
    "EVENT_LOGS":           ["EVENT_LOG_READ"],
    "PERSISTENCE":          ["PERSISTENCE_READ"],
    "FILESYSTEM":           ["FILE_READ"],
    "STARTUP_ITEMS":        ["PERSISTENCE_READ"],
    "BROWSER_ARTIFACTS":    ["FILE_READ"],
    "HASHES":               ["FILE_READ", "FILE_HASH"],
}

# All known safe read-only capabilities
ALL_READ_CAPABILITIES = {
    "PROCESS_READ",
    "NETWORK_READ",
    "SYSTEM_INFO_READ",
    "FILE_READ",
    "FILE_HASH",
    "EVENT_LOG_READ",
    "PERSISTENCE_READ",
}


def extract_required_capabilities(ir: dict) -> set[str]:
    """Walk the IR and return all capabilities needed to execute it."""
    caps: set[str] = set()
    for scope in ir.get("scopes", []):
        for op in scope.get("operations", []):
            if op.get("op") == "COLLECT":
                target = op.get("target", "")
                for cap in CAPABILITY_MAP.get(target, []):
                    caps.add(cap)
    return caps


def check_capabilities(
    required: set[str],
    granted: set[str] | None = None,
) -> dict[str, Any]:
    """
    Validate requested capabilities against granted set.

    If *granted* is None, default read-only policy allows all known read capabilities.
    Returns a policy decision dict.
    """
    if granted is None:
        granted = ALL_READ_CAPABILITIES

    decisions: list[dict] = []
    denied: list[str] = []

    for cap in sorted(required):
        allowed = cap in granted
        decisions.append({
            "capability": cap,
            "decision": "ALLOW" if allowed else "DENY",
        })
        if not allowed:
            denied.append(cap)

    return {
        "requested_capabilities": sorted(required),
        "granted_capabilities": sorted(granted),
        "decisions": decisions,
        "overall": "ALLOW" if not denied else "DENY",
        "denied": denied,
    }


def enforce_policy(ir: dict, granted: set[str] | None = None) -> dict:
    """
    Extract capabilities from IR, check against policy, raise if denied.
    Returns the policy decision dict on success.
    """
    required = extract_required_capabilities(ir)
    decision = check_capabilities(required, granted)

    if decision["overall"] == "DENY":
        raise PolicyDeniedError(
            capability=", ".join(decision["denied"]),
            reason="Required capabilities not granted by policy",
        )

    return decision
