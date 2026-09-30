"""JOCKY Runtime — IR Execution Errors"""


class JockyRuntimeError(Exception):
    """Base error for IR execution failures."""
    pass


class UnsupportedOperationError(JockyRuntimeError):
    """Operation opcode is not registered."""
    def __init__(self, op: str):
        super().__init__(f"Unsupported operation: {op}")
        self.op = op


class CollectorError(JockyRuntimeError):
    """A collector failed during evidence collection."""
    def __init__(self, collector: str, detail: str):
        super().__init__(f"Collector '{collector}' failed: {detail}")
        self.collector = collector
        self.detail = detail


class PolicyDeniedError(JockyRuntimeError):
    """Policy engine denied execution."""
    def __init__(self, capability: str, reason: str = ""):
        super().__init__(f"Policy denied capability '{capability}': {reason}")
        self.capability = capability
        self.reason = reason


class CapabilityError(JockyRuntimeError):
    """Required capability not available on this platform."""
    def __init__(self, capability: str):
        super().__init__(f"Capability not available: {capability}")
        self.capability = capability
