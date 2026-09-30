"""JOCKY Runtime — IR Executor

The core execution engine: consumes JOCKY Forensic IR and drives
real evidence collection through registered platform collectors.

Execution flow:
    IR JSON → validate → policy check → for each scope →
        for each operation → dispatch to collector/handler → evidence
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from agent.runtime.execution_context import ExecutionContext
from agent.runtime.operation_registry import get_collector, register_all_collectors
from agent.runtime.capability_checker import enforce_policy, extract_required_capabilities
from agent.runtime.errors import (
    JockyRuntimeError,
    UnsupportedOperationError,
    CollectorError,
)


class IRExecutor:
    """
    Interprets JOCKY Forensic IR and executes operations against the
    local platform using registered collectors.
    """

    def __init__(self, mode: str = "live"):
        self.mode = mode
        self._registered = False

    def _ensure_registered(self):
        if not self._registered:
            register_all_collectors()
            self._registered = True

    def execute(
        self,
        ir: dict,
        context: ExecutionContext | None = None,
        granted_capabilities: set[str] | None = None,
    ) -> ExecutionContext:
        """
        Execute an IR program.

        Args:
            ir: Parsed JOCKY Forensic IR dict
            context: Optional pre-configured execution context
            granted_capabilities: Set of allowed capabilities (None = default read-only policy)

        Returns:
            ExecutionContext with all collected evidence, findings, errors
        """
        self._ensure_registered()

        if context is None:
            context = ExecutionContext()
        context.mode = self.mode

        # ── Start ─────────────────────────────────────────────────
        context.start()
        context.add_log(f"IR version: {ir.get('version', 'unknown')}")
        context.add_log(f"Platform: {context.platform_name}")
        context.add_log(f"Mode: {self.mode}")

        # ── Policy check ──────────────────────────────────────────
        try:
            policy_decision = enforce_policy(ir, granted_capabilities)
            context.granted_capabilities = set(policy_decision["granted_capabilities"])
            context.add_log(f"Policy check: {policy_decision['overall']} — "
                          f"{len(policy_decision['decisions'])} capabilities evaluated")
        except Exception as e:
            context.add_error(f"Policy check failed: {e}")
            context.finish()
            return context

        # ── Execute scopes ────────────────────────────────────────
        scopes = ir.get("scopes", [])
        context.add_log(f"Executing {len(scopes)} scope(s)")

        for scope_idx, scope in enumerate(scopes):
            scope_type = scope.get("scope_type", "unknown")
            scope_name = scope.get("name", f"scope_{scope_idx}")
            context.add_log(f"Scope [{scope_idx}]: {scope_type} '{scope_name}'")

            operations = scope.get("operations", [])
            collected_data: dict[str, list[dict]] = {}

            for op_idx, operation in enumerate(operations):
                opcode = operation.get("op", "")
                target = operation.get("target", "")
                arguments = operation.get("arguments", {})

                context.add_log(f"  Op [{op_idx}]: {opcode} {target}")

                try:
                    if opcode == "COLLECT":
                        results = self._handle_collect(target, arguments, context)
                        collected_data.setdefault(target, []).extend(results)

                    elif opcode == "FILTER":
                        if target in collected_data:
                            filtered = self._handle_filter(
                                collected_data[target], arguments, context
                            )
                            collected_data[target] = filtered
                            context.add_log(f"    Filtered {target}: {len(filtered)} items remain")
                        else:
                            context.add_log(f"    FILTER skipped — no collected data for {target}")

                    elif opcode == "ANALYZE":
                        context.add_log(f"    ANALYZE {target} — deferred to central analysis")

                    elif opcode == "GENERATE_TIMELINE":
                        context.add_log("    GENERATE_TIMELINE — deferred to central server")

                    elif opcode == "GENERATE_REPORT":
                        context.add_log("    GENERATE_REPORT — deferred to central server")

                    else:
                        context.add_log(f"    Unknown opcode: {opcode}")

                except CollectorError as e:
                    context.add_error(f"Collector error in {opcode} {target}: {e}")
                except Exception as e:
                    context.add_error(f"Unexpected error in {opcode} {target}: {e}")

        # ── Finish ────────────────────────────────────────────────
        context.finish()
        return context

    def _handle_collect(
        self,
        target: str,
        arguments: dict,
        context: ExecutionContext,
    ) -> list[dict]:
        """Dispatch a COLLECT operation to the appropriate collector."""
        collector = get_collector(target, context.platform_name)

        if collector is None:
            context.add_log(f"    No collector registered for {target} on {context.platform_name}")
            context.add_error(f"No collector for {target} on {context.platform_name}")
            return []

        try:
            payloads = collector.collect(context, arguments)
            context.add_log(f"    Collected {len(payloads)} {target} items")

            # Wrap each payload as a normalized evidence record
            type_map = {
                "PROCESSES": "PROCESS",
                "NETWORK_CONNECTIONS": "NETWORK_CONNECTION",
                "SYSTEM_INFO": "SYSTEM_INFO",
                "FILE_HASH": "FILE_METADATA",
                "FILESYSTEM": "FILE_METADATA",
                "EVENT_LOGS": "EVENT_LOG",
                "PERSISTENCE": "PERSISTENCE_ITEM",
            }
            evidence_type = type_map.get(target, target)
            collector_name = target.lower()

            for payload in payloads:
                context.add_evidence(evidence_type, collector_name, payload)

            return payloads

        except Exception as e:
            raise CollectorError(target, str(e))

    def _handle_filter(
        self,
        data: list[dict],
        arguments: dict,
        context: ExecutionContext,
    ) -> list[dict]:
        """Apply a filter condition to collected data."""
        condition = arguments.get("condition", {})
        if not condition:
            return data

        field_name = condition.get("field", "")
        operator = condition.get("operator", condition.get("op", ""))
        value = condition.get("value", condition.get("right", {}).get("value"))

        # Normalize: handle old IR format where condition is nested
        if not field_name and "left" in condition:
            field_name = condition["left"].get("name", "")
        if not operator and "op" in condition:
            operator = condition["op"]
        if value is None and "right" in condition:
            right = condition["right"]
            value = right.get("value") if isinstance(right, dict) else right

        if not field_name or not operator:
            return data

        filtered = []
        for item in data:
            item_value = item.get(field_name)
            if item_value is None:
                continue

            try:
                if operator == ">" and float(item_value) > float(value):
                    filtered.append(item)
                elif operator == "<" and float(item_value) < float(value):
                    filtered.append(item)
                elif operator == ">=" and float(item_value) >= float(value):
                    filtered.append(item)
                elif operator == "<=" and float(item_value) <= float(value):
                    filtered.append(item)
                elif operator == "==" and str(item_value) == str(value):
                    filtered.append(item)
                elif operator == "!=" and str(item_value) != str(value):
                    filtered.append(item)
                elif operator == "in" and item_value in (value if isinstance(value, list) else [value]):
                    filtered.append(item)
            except (ValueError, TypeError):
                continue

        return filtered
