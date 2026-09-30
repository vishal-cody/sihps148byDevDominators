"""JOCKY Collectors — Base interface and helpers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from agent.runtime.execution_context import ExecutionContext


class BaseCollector(ABC):
    """Abstract base for all forensic evidence collectors."""

    name: str = "base"

    @abstractmethod
    def collect(self, context: ExecutionContext, arguments: dict[str, Any] | None = None) -> list[dict]:
        """
        Collect evidence from the local system.

        Returns a list of payload dicts (raw evidence data).
        Each payload will be wrapped in a normalized evidence record by the executor.
        """
        ...
